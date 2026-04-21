"""
builder/views.py
────────────────
Handles resume form rendering, LaTeX PDF generation, AI text enhancement,
and the user dashboard.
"""

import os
import json
import shutil
import subprocess
import tempfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

import google.generativeai as genai

from .models import ResumeData


# ════════════════════════════════════════════════
#  UTILITY — Find pdflatex
# ════════════════════════════════════════════════

def find_pdflatex():
    """Locate pdflatex executable. Checks PATH first, then common install locations."""
    import shutil
    path = shutil.which('pdflatex')
    if path:
        return path

    # Common MiKTeX install locations on Windows
    common_paths = [
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe'),
        r'C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe',
        r'C:\miktex\miktex\bin\x64\pdflatex.exe',
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p

    return 'pdflatex'  # Last resort — hope it's in PATH


# ════════════════════════════════════════════════
#  UTILITY — LaTeX Escaping
# ════════════════════════════════════════════════

def escape_latex(text):
    """Escape special LaTeX characters in user-provided text."""
    if not text:
        return ""
    special_chars = {
        '\\': r'\textbackslash{}',   # Must be first to avoid double escaping
        '&':  r'\&',
        '%':  r'\%',
        '$':  r'\$',
        '#':  r'\#',
        '_':  r'\_',
        '{':  r'\{',
        '}':  r'\}',
        '~':  r'\textasciitilde{}',
        '^':  r'\textasciicircum{}',
    }
    for char, escaped in special_chars.items():
        text = text.replace(char, escaped)
    return text


# ════════════════════════════════════════════════
#  VIEW — Home (Resume Builder Form)
# ════════════════════════════════════════════════

@login_required(login_url='/login/')
def home(request):
    """Renders the frontend HTML form."""
    return render(request, 'index.html')


# ════════════════════════════════════════════════
#  VIEW — Generate Resume (POST handler)
# ════════════════════════════════════════════════

@login_required(login_url='/login/')
def generate_resume(request):
    """
    Processes form data → saves to DB → injects into LaTeX template
    → compiles PDF → redirects to dashboard.
    """
    if request.method != 'POST':
        return HttpResponse("Invalid request method.", status=400)

    # ── 1. EXTRACT RAW DATA FROM FORM ──────────────────────────
    raw_name     = request.POST.get('name', '').strip()
    raw_subtitle = request.POST.get('subtitle', '').strip()
    raw_phone    = request.POST.get('phone', '').strip()
    raw_email    = request.POST.get('email', '').strip()
    raw_github   = request.POST.get('github', '').strip()
    raw_linkedin = request.POST.get('linkedin', '').strip()

    # ── Validate required fields ──
    if not all([raw_name, raw_phone, raw_email]):
        return HttpResponse(
            "<h1>Missing Required Fields</h1>"
            "<p>Name, phone, and email are required.</p>"
            '<p><a href="/home/">Go back</a></p>',
            status=400
        )

    # ── 2. PARSE DYNAMIC SECTIONS ──────────────────────────────

    # Education
    education_list = []
    for year, degree, institute, cgpa in zip(
        request.POST.getlist('edu_year[]'),
        request.POST.getlist('edu_degree[]'),
        request.POST.getlist('edu_institute[]'),
        request.POST.getlist('edu_cgpa[]'),
    ):
        if degree.strip():
            education_list.append({
                'year': year.strip(),
                'degree': degree.strip(),
                'college': institute.strip(),
                'cgpa': cgpa.strip(),
            })

    # Projects
    projects_list = []
    for title, tech, desc in zip(
        request.POST.getlist('proj_title[]'),
        request.POST.getlist('proj_tech[]'),
        request.POST.getlist('proj_desc[]'),
    ):
        if title.strip():
            projects_list.append({
                'title': title.strip(),
                'tech': tech.strip(),
                'description': desc.strip(),
            })

    # Positions of Responsibility / Experience
    experience_list = []
    for role, date, desc in zip(
        request.POST.getlist('resp_title[]'),
        request.POST.getlist('resp_date[]'),
        request.POST.getlist('resp_desc[]'),
    ):
        if role.strip():
            experience_list.append({
                'role': role.strip(),
                'duration': date.strip(),
                'description': desc.strip(),
            })

    # Skills (list of strings like "Languages: C++, Python")
    skills_list = [s.strip() for s in request.POST.getlist('skill[]') if s.strip()]

    # Achievements (list of strings)
    achievements_list = [a.strip() for a in request.POST.getlist('achievement[]') if a.strip()]

    # ── 3. SAVE TO DATABASE ────────────────────────────────────
    resume_obj = ResumeData.objects.create(
        user=request.user,
        name=raw_name,
        email=raw_email,
        phone=raw_phone,
        github=raw_github,
        linkedin=raw_linkedin,
        summary=raw_subtitle,
        education=education_list,
        projects=projects_list,
        experience=experience_list,
        skills=skills_list,
        achievements=achievements_list,
    )

    # ── 4. BUILD LATEX CONTENT ─────────────────────────────────

    # -- Education section (uses \resumeSubheading) --
    education_latex = ""
    for i, edu in enumerate(education_list):
        education_latex += (
            f"\\resumeSubheading\n"
            f"  {{{escape_latex(edu['college'])}}}\n"
            f"  {{CGPA: {escape_latex(edu['cgpa'])}}}\n"
            f"  {{{escape_latex(edu['degree'])}}}\n"
            f"  {{{escape_latex(edu['year'])}}}\n"
        )
        if i < len(education_list) - 1:
            education_latex += "\n\\vspace{-6pt}\n\n"

    # -- Skills section (uses \item \textbf{Category:} skills) --
    skills_latex = ""
    for skill in skills_list:
        if ":" in skill:
            cat, sk = skill.split(":", 1)
            skills_latex += f"\\item \\textbf{{{escape_latex(cat.strip())}:}} {escape_latex(sk.strip())}\n\n"
        else:
            skills_latex += f"\\item {escape_latex(skill)}\n\n"

    # -- Positions of Responsibility (uses \resumePOR + itemize) --
    resp_latex = ""
    for exp in experience_list:
        resp_latex += f"\\resumePOR{{{escape_latex(exp['role'])}}}{{}}{{{escape_latex(exp['duration'])}}}\n"
        if exp['description']:
            resp_latex += "\\resumeItemListStart\n"
            for bullet in exp['description'].split('\n'):
                if bullet.strip():
                    resp_latex += f"    \\item {escape_latex(bullet.strip())}\n"
            resp_latex += "\\resumeItemListEnd\n"
        resp_latex += "\n"

    # -- Projects (uses \resumePOR + itemize) --
    projects_latex = ""
    for proj in projects_list:
        projects_latex += f"\\resumePOR{{{escape_latex(proj['title'])}}}{{{escape_latex(proj['tech'])}}}{{}}\n"
        if proj['description']:
            projects_latex += "\\resumeItemListStart\n"
            for bullet in proj['description'].split('\n'):
                if bullet.strip():
                    projects_latex += f"    \\item {escape_latex(bullet.strip())}\n"
            projects_latex += "\\resumeItemListEnd\n"
        projects_latex += "\n\\vspace{-4pt}\n\n"

    # -- Achievements (uses \resumePOR) --
    achievements_latex = ""
    for ach in achievements_list:
        achievements_latex += f"\\vspace{{-4pt}}\n\n\\resumePOR{{{escape_latex(ach)}}}{{}}{{}}\n\n"

    # ── 5. LOAD TEMPLATE & REPLACE PLACEHOLDERS ───────────────
    template_path = os.path.join(settings.TEMPLATES_DIR, 'resume_template.tex')
    with open(template_path, 'r', encoding='utf-8') as f:
        tex_content = f.read()

    # Build GitHub/LinkedIn display values
    github_url = raw_github if raw_github.startswith('http') else f'https://{raw_github}'
    github_text = escape_latex(raw_github.replace('https://', '').replace('http://', ''))

    linkedin_url = raw_linkedin if raw_linkedin.startswith('http') else f'https://{raw_linkedin}'
    linkedin_text = escape_latex(raw_linkedin.replace('https://', '').replace('http://', ''))

    replacements = {
        '<<NAME>>':                 escape_latex(raw_name.upper()),
        '<<SUBTITLE>>':            escape_latex(raw_subtitle),
        '<<PHONE>>':               escape_latex(raw_phone),
        '<<EMAIL>>':               escape_latex(raw_email),
        '<<GITHUB_URL>>':          github_url,
        '<<GITHUB_TEXT>>':         github_text,
        '<<LINKEDIN_URL>>':        linkedin_url,
        '<<LINKEDIN_TEXT>>':       linkedin_text,
        '<<EDUCATION_ITEMS>>':     education_latex,
        '<<SKILL_ITEMS>>':         skills_latex,
        '<<RESPONSIBILITY_ITEMS>>': resp_latex,
        '<<PROJECT_ITEMS>>':       projects_latex,
        '<<ACHIEVEMENT_ITEMS>>':   achievements_latex,
    }

    for key, value in replacements.items():
        tex_content = tex_content.replace(key, value)

    # ── 6. COMPILE LATEX → PDF ─────────────────────────────────
    with tempfile.TemporaryDirectory() as tempdir:
        tex_file_path = os.path.join(tempdir, 'resume.tex')
        pdf_file_path = os.path.join(tempdir, 'resume.pdf')

        with open(tex_file_path, 'w', encoding='utf-8') as f:
            f.write(tex_content)

        try:
            pdflatex_path = find_pdflatex()
            subprocess.run(
                [pdflatex_path, '-interaction=nonstopmode', '-halt-on-error', 'resume.tex'],
                cwd=tempdir,
                check=True,
                capture_output=True,
                text=True,
            )

            # ── 7. SAVE PDF TO MEDIA FOLDER ───────────────────
            resumes_dir = os.path.join(settings.MEDIA_ROOT, 'resumes')
            os.makedirs(resumes_dir, exist_ok=True)

            final_pdf_path = os.path.join(resumes_dir, f'resume_{resume_obj.id}.pdf')
            shutil.copy(pdf_file_path, final_pdf_path)

            return redirect('dashboard')

        except subprocess.CalledProcessError as e:
            # LaTeX compilation failed — clean up DB entry
            resume_obj.delete()
            error_log = e.stdout or e.stderr or "No error output captured."
            return HttpResponse(
                f"<h1>LaTeX Compilation Failed</h1>"
                f"<p>There was an error generating your resume PDF. "
                f"Please check your input for special characters.</p>"
                f"<pre style='max-height:400px;overflow:auto;background:#f5f5f5;"
                f"padding:16px;border-radius:8px;font-size:12px;'>{error_log}</pre>"
                f'<br><a href="/home/">← Go Back</a>',
                status=500,
            )


# ════════════════════════════════════════════════
#  VIEW — Dashboard
# ════════════════════════════════════════════════

@login_required(login_url='/login/')
def dashboard(request):
    """Shows all resumes created by the logged-in user."""
    resumes = ResumeData.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'dashboard.html', {'resumes': resumes})


# ════════════════════════════════════════════════
#  VIEW — Delete Resume
# ════════════════════════════════════════════════

@login_required(login_url='/login/')
def delete_resume(request, resume_id):
    """Deletes a resume and its PDF file."""
    if request.method == 'POST':
        try:
            resume = ResumeData.objects.get(id=resume_id, user=request.user)
            # Delete the PDF file if it exists
            pdf_path = os.path.join(settings.MEDIA_ROOT, 'resumes', f'resume_{resume.id}.pdf')
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            resume.delete()
        except ResumeData.DoesNotExist:
            pass
    return redirect('dashboard')


# ════════════════════════════════════════════════
#  VIEW — Download Resume (proper PDF headers)
# ════════════════════════════════════════════════

@login_required(login_url='/login/')
def download_resume(request, resume_id):
    """Serves the PDF with proper Content-Disposition so browsers save it as Name_Resume.pdf."""
    from django.http import FileResponse

    try:
        resume = ResumeData.objects.get(id=resume_id, user=request.user)
    except ResumeData.DoesNotExist:
        return HttpResponse("Resume not found.", status=404)

    pdf_path = os.path.join(settings.MEDIA_ROOT, 'resumes', f'resume_{resume.id}.pdf')
    if not os.path.exists(pdf_path):
        return HttpResponse("PDF file not found.", status=404)

    # Sanitize name for filename
    safe_name = resume.name.replace(' ', '_').replace('/', '-')
    filename = f"{safe_name}_Resume.pdf"

    response = FileResponse(
        open(pdf_path, 'rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=filename,
    )
    return response


# ════════════════════════════════════════════════
#  API — Rename Resume
# ════════════════════════════════════════════════

@login_required(login_url='/login/')
def rename_resume(request, resume_id):
    """Renames a resume entry."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            new_name = data.get('name', '').strip()
        except (json.JSONDecodeError, AttributeError):
            new_name = request.POST.get('name', '').strip()

        if not new_name:
            return JsonResponse({'error': 'Name cannot be empty.'}, status=400)

        try:
            resume = ResumeData.objects.get(id=resume_id, user=request.user)
            resume.name = new_name
            resume.save()
            return JsonResponse({'success': True, 'name': new_name})
        except ResumeData.DoesNotExist:
            return JsonResponse({'error': 'Resume not found.'}, status=404)

    return JsonResponse({'error': 'POST required.'}, status=405)


# ════════════════════════════════════════════════
#  API — AI Text Enhancement
# ════════════════════════════════════════════════

def enhance_text(request):
    """API Endpoint to enhance resume bullet points using Gemini AI with token optimization."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        data = json.loads(request.body)
        original_text = data.get('text', '').strip()

        if not original_text:
            return JsonResponse({'error': 'No text provided'}, status=400)

        # Fallback: Simple enhancement without API if needed
        def simple_enhance(text):
            """Fallback enhancement using basic text processing."""
            lines = text.split('\n')
            enhanced = []
            action_verbs = [
                'Developed', 'Implemented', 'Optimized', 'Designed', 'Created',
                'Enhanced', 'Improved', 'Spearheaded', 'Collaborated', 'Managed'
            ]
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Remove markdown bullets
                line = line.lstrip('*-•').strip()
                # Add action verb if missing
                if line and not any(line.startswith(verb) for verb in action_verbs):
                    line = f"* Developed and enhanced {line.lower()}"
                else:
                    line = f"* {line}"
                enhanced.append(line)
            
            return '\n'.join(enhanced) if enhanced else original_text

        try:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel(
                'gemini-2.0-flash',
                generation_config={
                    "max_output_tokens": 300  # Limit to 300 tokens to reduce consumption
                }
            )
            
            prompt = f"""Rewrite the following resume bullet points to be professional and action-oriented.
Use strong action verbs. Do NOT add fake metrics or numbers.
Return ONLY the enhanced text (no markdown, no asterisks).

Text: {original_text}"""

            response = model.generate_content(prompt)
            cleaned = response.text.replace('*', '').replace('•', '').strip()
            return JsonResponse({'enhanced_text': cleaned})
        
        except Exception as api_error:
            error_str = str(api_error)
            print(f"API Error: {error_str}")  # Log for debugging
            
            # If API fails (quota exceeded, key invalid, etc.), use fallback
            fallback_text = simple_enhance(original_text)
            return JsonResponse({
                'enhanced_text': fallback_text,
                'warning': 'Using basic enhancement (API unavailable)'
            }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)
