# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from .forms import ResumeForm
# from .models import ResumeData
# from .services import generate_professional_resume
# from .pdf_generator import create_resume_pdf
#
#
# @login_required
# def resume_builder(request):
#     if request.method == "POST":
#         form = ResumeForm(request.POST)
#
#         if form.is_valid():
#             resume_obj = form.save(commit=False)
#             resume_obj.user = request.user
#
#             # === Handle Dynamic Fields (Experience, Education, Projects) ===
#             # Experience
#             experience_list = []
#             exp_count = int(request.POST.get('exp_count', 0))
#             for i in range(exp_count):
#                 if request.POST.get(f'exp_role_{i}'):
#                     experience_list.append({
#                         'role': request.POST.get(f'exp_role_{i}'),
#                         'company': request.POST.get(f'exp_company_{i}'),
#                         'duration': request.POST.get(f'exp_duration_{i}'),
#                         'description': request.POST.get(f'exp_description_{i}', ''),
#                     })
#             resume_obj.experience = experience_list
#
#             # Education
#             education_list = []
#             edu_count = int(request.POST.get('edu_count', 0))
#             for i in range(edu_count):
#                 if request.POST.get(f'edu_degree_{i}'):
#                     education_list.append({
#                         'degree': request.POST.get(f'edu_degree_{i}'),
#                         'college': request.POST.get(f'edu_college_{i}'),
#                         'year': request.POST.get(f'edu_year_{i}'),
#                     })
#             resume_obj.education = education_list
#
#             # Projects
#             projects_list = []
#             proj_count = int(request.POST.get('proj_count', 0))
#             for i in range(proj_count):
#                 if request.POST.get(f'proj_title_{i}'):
#                     projects_list.append({
#                         'title': request.POST.get(f'proj_title_{i}'),
#                         'description': request.POST.get(f'proj_description_{i}', ''),
#                     })
#             resume_obj.projects = projects_list
#
#             resume_obj.save()
#
#             # Prepare data for AI
#             raw_data = {
#                 "name": resume_obj.name,
#                 "email": resume_obj.email,
#                 "phone": resume_obj.phone,
#                 "linkedin": resume_obj.linkedin,
#                 "summary": resume_obj.summary,
#                 "experience": resume_obj.experience,
#                 "education": resume_obj.education,
#                 "skills": resume_obj.skills,
#                 "projects": resume_obj.projects,
#             }
#
#             # GenAI + PDF Generation
#             optimized_data = generate_professional_resume(raw_data)
#             pdf_url = create_resume_pdf(resume_obj.id, optimized_data)
#
#             return render(request, 'success.html', {'pdf_url': pdf_url})
#
#     else:
#         form = ResumeForm()
#
#     return render(request, 'index.html', {'form': form})
#
#
# @login_required
# def dashboard(request):
#     resumes = ResumeData.objects.filter(user=request.user).order_by('-created_at')
#     return render(request, 'dashboard.html', {'resumes': resumes})

import os
from django.db import models
import shutil
import json
import subprocess
import tempfile
from django.shortcuts import render,redirect
from django.http import  HttpResponse
from django.conf import settings
from .models import ResumeData
from django.contrib.auth.decorators import login_required
# Configure Gemini AI
from django.http import JsonResponse # Add this to imports
from .services import enhance_resume_text
import google.generativeai as genai
def enhance_text(request):
    """API Endpoint to enhance resume bullet points using Gemini."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            original_text = data.get('text', '')

            if not original_text:
                return JsonResponse({'error': 'No text provided'}, status=400)

            # The Prompt instructing the AI how to behave
            prompt = f"""
            Rewrite the following resume bullet points to be highly professional, impactful, and action-oriented.
            Use strong action verbs. Do not add fake metrics or numbers that aren't there.
            Return ONLY the enhanced bullet points as plain text separated by newlines.
            Do NOT use markdown (like asterisks or bullet characters like -, *, •).
            Just return the raw sentences.

            Original Text:
            {original_text}
            """
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(prompt)

            # Clean up any potential markdown asterisks the AI might still sneak in
            cleaned_response = response.text.replace('*', '').replace('•', '').strip()

            return JsonResponse({'enhanced_text': cleaned_response})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def escape_latex(text):
    """Escapes special characters for LaTeX."""
    if not text:
        return ""
    # special_chars = {
    #     '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
    #     '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}', '\\': r'\textbackslash{}'
    # }
    special_chars = {
        '\\': r'\textbackslash{}',  # Must be first to avoid double escaping
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}'
    }
    for char, escaped_char in special_chars.items():
        text = text.replace(char, escaped_char)
    return text
    # res = text.replace('\\', replacements['\\'])
    # for char, escaped in replacements.items():
    #     if char != '\\':
    #         res = res.replace(char, escaped)
    # return res

@login_required(login_url='/login/')
def home(request):
    """Renders the frontend HTML form."""
    return render(request, 'index.html')

@login_required(login_url='/login/')
def generate_resume(request):
    """Processes form data, saves to DB, generates the PDF, and redirects to dashboard."""
    if request.method != 'POST':
        return HttpResponse("Invalid request method.", status=400)

    # === 1. EXTRACT RAW DATA FROM FORM ===
    raw_name = request.POST.get('name', '')
    raw_subtitle = request.POST.get('subtitle', '')
    raw_phone = request.POST.get('phone', '')
    raw_email = request.POST.get('email', '')
    raw_github = request.POST.get('github', '')

    # === 2. FORMAT DATA FOR THE DATABASE (JSON) ===
    # We pack the array data into lists of dictionaries so your model can save them as JSONField
    education_list = []
    for y, d, i, c in zip(request.POST.getlist('edu_year[]'), request.POST.getlist('edu_degree[]'),
                          request.POST.getlist('edu_institute[]'), request.POST.getlist('edu_cgpa[]')):
        education_list.append({'year': y, 'degree': d, 'college': i, 'cgpa': c})

    projects_list = []
    for t, tech, desc in zip(request.POST.getlist('proj_title[]'), request.POST.getlist('proj_tech[]'),
                             request.POST.getlist('proj_desc[]')):
        projects_list.append({'title': t, 'tech': tech, 'description': desc})

    experience_list = []
    for t, date, desc in zip(request.POST.getlist('resp_title[]'), request.POST.getlist('resp_date[]'),
                             request.POST.getlist('resp_desc[]')):
        experience_list.append({'role': t, 'duration': date, 'description': desc})

    skills_list = request.POST.getlist('skill[]')

    # === 3. SAVE TO DATABASE ===
    resume_obj = ResumeData.objects.create(
        user=request.user,
        name=raw_name,
        email=raw_email,
        phone=raw_phone,
        linkedin=raw_github,  # Mapping github to your linkedin db field
        summary=raw_subtitle,  # Mapping subtitle to your summary db field
        education=education_list,
        projects=projects_list,
        experience=experience_list,
        skills=skills_list
    )

    # === 4. PREPARE LATEX DATA ===
    # (We escape everything for LaTeX just like you did before)
    name = escape_latex(raw_name.upper())
    subtitle = escape_latex(raw_subtitle)
    phone = escape_latex(raw_phone)
    email = escape_latex(raw_email)
    github = escape_latex(raw_github)

    education_latex = ""
    for edu in education_list:
        education_latex += f"{escape_latex(edu['year'])} & {escape_latex(edu['degree'])} & {escape_latex(edu['college'])} & {escape_latex(edu['cgpa'])} \\\\ \\hline\n"

    achievements_latex = ""
    for ach in request.POST.getlist('achievement[]'):
        if ach.strip(): achievements_latex += f"\\item {escape_latex(ach)}\n"

    projects_latex = ""
    for proj in projects_list:
        projects_latex += f"\\projectheader{{{escape_latex(proj['title'])}}}{{{escape_latex(proj['tech'])}}}\n\\begin{{cvitemize}}\n"
        for bullet in proj['description'].split('\n'):
            if bullet.strip(): projects_latex += f"    \\item {escape_latex(bullet.strip())}\n"
        projects_latex += "\\end{cvitemize}\n\\vspace{1ex}\n"

    skills_latex = ""
    for skill in skills_list:
        if skill.strip():
            if ":" in skill:
                cat, sk = skill.split(":", 1)
                skills_latex += f"\\item \\textbf{{{escape_latex(cat.strip())}:}} {escape_latex(sk.strip())}\n"
            else:
                skills_latex += f"\\item {escape_latex(skill.strip())}\n"

    resp_latex = ""
    for exp in experience_list:
        resp_latex += f"\\noindent\\textbf{{{escape_latex(exp['role'])}}} \\hfill {escape_latex(exp['duration'])}\n\\begin{{cvitemize}}\n"
        for bullet in exp['description'].split('\n'):
            if bullet.strip(): resp_latex += f"    \\item {escape_latex(bullet.strip())}\n"
        resp_latex += "\\end{cvitemize}\n\\vspace{1ex}\n"

    # === 5. COMPILE LATEX PDF ===
    template_path = os.path.join(settings.BASE_DIR, 'templates', 'resume_template.tex')
    with open(template_path, 'r', encoding='utf-8') as f:
        tex_content = f.read()

    context = {
        '<<NAME>>': name, '<<SUBTITLE>>': subtitle, '<<PHONE>>': phone,
        '<<EMAIL>>': email, '<<GITHUB_URL>>': raw_github, '<<GITHUB_TEXT>>': escape_latex(raw_github),'<<EDUCATION_ROWS>>': education_latex,
        '<<ACHIEVEMENT_ITEMS>>': achievements_latex, '<<PROJECT_ITEMS>>': projects_latex,
        '<<SKILL_ITEMS>>': skills_latex, '<<RESPONSIBILITY_ITEMS>>': resp_latex,
    }
    for key, value in context.items():
        tex_content = tex_content.replace(key, value)

    with tempfile.TemporaryDirectory() as tempdir:
        tex_file_path = os.path.join(tempdir, 'resume.tex')
        pdf_file_path = os.path.join(tempdir, 'resume.pdf')

        with open(tex_file_path, 'w', encoding='utf-8') as f:
            f.write(tex_content)
        try:
            # We add capture_output=True so e.stderr actually contains the error message
            # We add --halt-on-error to ensure it stops if there's a REAL LaTeX issue
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'resume.tex'],
                cwd=tempdir,
                check=True,
                capture_output=True,
                text=True  # This returns strings instead of bytes, so no .decode() needed!
            )

            # === 6. SAVE PDF TO MEDIA FOLDER ===
            resumes_dir = os.path.join(settings.MEDIA_ROOT, 'resumes')
            os.makedirs(resumes_dir, exist_ok=True)

            final_pdf_path = os.path.join(resumes_dir, f'resume_{resume_obj.id}.pdf')
            shutil.copy(pdf_file_path, final_pdf_path)

            return redirect('dashboard')

        except subprocess.CalledProcessError as e:
            # Since we used text=True, e.stderr is already a string.
            # If it's still None for some reason, we provide a fallback.
            error_log = e.stderr if e.stderr else e.stdout

            # Logic: If the PDF was actually created despite the "Major Issue" warning,
            # you might want to proceed anyway. But usually, we catch the error:
            resume_obj.delete()
            return HttpResponse(
                f"<h1>LaTeX Compilation Failed</h1>"
                f"<p>MiKTeX is complaining about updates, but the real error might be below:</p>"
                f"<pre>{error_log}</pre>",
                status=500
            )

        try:
            subprocess.run(['pdflatex', '-interaction=nonstopmode', 'resume.tex'],
                           cwd=tempdir, check=True,capture_output=True,text=False)
            # subprocess.run(['pdflatex', '-interaction=nonstopmode', 'resume.tex'],
            #                cwd=tempdir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # === 6. SAVE PDF TO MEDIA FOLDER ===
            # Ensure the media/resumes directory exists
            resumes_dir = os.path.join(settings.MEDIA_ROOT, 'resumes')
            os.makedirs(resumes_dir, exist_ok=True)

            # Copy the generated PDF from the temp folder to your Django media folder
            final_pdf_path = os.path.join(resumes_dir, f'resume_{resume_obj.id}.pdf')
            shutil.copy(pdf_file_path, final_pdf_path)

            # === 7. REDIRECT TO DASHBOARD ===
            return redirect('dashboard')

        except subprocess.CalledProcessError as e:
            # If LaTeX fails, delete the DB entry so we don't have broken records
            resume_obj.delete()
            error_message = e.stderr.decode() if e.stderr else "No error output captured from pdflatex."
            return HttpResponse(f"<h1>LaTeX Compilation Failed</h1><pre>{error_message}</pre>", status=500)
@login_required(login_url='/login/')
def dashboard(request):
    resumes = ResumeData.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'dashboard.html', {'resumes': resumes})

