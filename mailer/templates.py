from datetime import datetime


def _section_html(title: str, emoji: str, articles: list[dict]) -> str:
    items = ""
    for i, a in enumerate(articles, 1):
        summary = a.get("summary", "").strip()
        items += f"""
        <tr>
          <td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1a1a1a;">
              {i}. <a href="{a['url']}" style="color:#2563eb;text-decoration:none;">{a['title']}</a>
            </p>
            <p style="margin:0 0 4px;font-size:13px;color:#555;">{summary}</p>
            <p style="margin:0;font-size:11px;color:#999;">{a.get('source','')}</p>
          </td>
        </tr>"""

    return f"""
    <tr><td style="padding:20px 0 8px;">
      <h2 style="margin:0;font-size:18px;color:#1a1a1a;">{emoji} {title}</h2>
      <hr style="border:none;border-top:2px solid #2563eb;margin:8px 0 0;">
    </td></tr>
    {items}
    """


def render_newsletter(
    ai_articles: list[dict],
    startup_jobs_articles: list[dict],
    immigration_articles: list[dict],
) -> tuple[str, str]:
    date_str = datetime.now().strftime("%A, %B %d, %Y")

    sections_html = (
        _section_html("AI News", "🤖", ai_articles)
        + _section_html("Startups & Jobs", "🚀", startup_jobs_articles)
        + _section_html("US Immigration", "🇺🇸", immigration_articles)
    )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8f9fa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f9fa;">
    <tr><td align="center" style="padding:24px 16px;">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1);">

        <!-- Header -->
        <tr><td style="background:#2563eb;padding:28px 32px;">
          <h1 style="margin:0;color:#fff;font-size:24px;">Parks Tech USA Daily Brief</h1>
          <p style="margin:4px 0 0;color:#bfdbfe;font-size:14px;">{date_str}</p>
        </td></tr>

        <!-- Content -->
        <tr><td style="padding:0 32px 24px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            {sections_html}
          </table>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#f8f9fa;padding:20px 32px;border-top:1px solid #e5e7eb;">
          <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
            You're receiving this because you subscribed to Parks Tech USA Daily Brief.<br>
            To unsubscribe, reply with "unsubscribe" in the subject line. | parkstechusa.com
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    # Plain text version
    def plain_section(title, articles):
        lines = [f"\n{'='*50}", f"  {title}", f"{'='*50}"]
        for i, a in enumerate(articles, 1):
            lines.append(f"\n{i}. {a['title']}")
            lines.append(f"   {a.get('summary','')[:200]}")
            lines.append(f"   {a['url']}")
            lines.append(f"   Source: {a.get('source','')}")
        return "\n".join(lines)

    plain = f"PARKS TECH USA DAILY BRIEF — {date_str}\n"
    plain += plain_section("🤖 AI NEWS (Top 10)", ai_articles)
    plain += plain_section("🚀 STARTUPS & JOBS (Top 10)", startup_jobs_articles)
    plain += plain_section("🇺🇸 US IMMIGRATION (Top 5)", immigration_articles)
    plain += "\n\nTo unsubscribe, reply with 'unsubscribe' in the subject."

    return html, plain
