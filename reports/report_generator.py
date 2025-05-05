import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime

# Set up Jinja2 environment
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def generate_pdf_report(project_name, summary, total_tasks, completed_tasks, pending_tasks, blockers=None):
    # Load the HTML template
    template = env.get_template('daily_standup.html')

    # Prepare context data
    context = {
        "date": datetime.now().strftime("%B %d, %Y"),
        "project": project_name,
        "summary": summary,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "blockers": blockers if blockers else []
    }

    # Render the HTML with data
    rendered_html = template.render(context)

    # Output PDF location
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{project_name.lower()}_standup_report.pdf")

    # Generate PDF
    HTML(string=rendered_html).write_pdf(pdf_path)

    # print(f"✅ Report generated: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    generate_pdf_report(
        project_name="Sarthi",
        summary="Team is making good progress. No major blockers today.",
        total_tasks=12,
        completed_tasks=7,
        pending_tasks=5,
        blockers=["Waiting for API access", "Need UI designs for dashboard"]
    )
