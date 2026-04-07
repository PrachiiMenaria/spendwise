from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import ai_engine

mail = Mail()


def send_email(app, subject, recipient, body_text):
    with app.app_context():
        msg = Message(
            subject,
            sender=os.getenv("MAIL_USERNAME", "noreply@finora.app"),
            recipients=[recipient],
        )
        msg.body = body_text
        try:
            mail.send(msg)
            print(f"[Email] Sent to {recipient}")
        except Exception as e:
            print(f"[Email] Failed to send to {recipient}: {e}")


def weekly_ai_report_job(app):
    print("[Job] Running Weekly AI Report Email Job...")
    conn = ai_engine.get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email FROM users")
            users = cur.fetchall()
        for uid, uname, uemail in users:
            try:
                insights = ai_engine.generate_insights(uid)
                body = f"Hello {uname} ✨,\n\nHere is your Finora AI Weekly Report.\n\n"
                if insights:
                    body += "Top Insights:\n"
                    for ins in insights[:3]:
                        body += f"- {ins['message']}\n"
                else:
                    body += "You're perfectly on track this week. Keep it up!\n"
                body += "\nBest,\nFinora AI Engine"
                send_email(app, "Your Finora AI Weekly Insight", uemail, body)
            except Exception as e:
                print(f"[Job] Could not generate report for user {uid}: {e}")
    finally:
        conn.close()


def monthly_budget_reminder(app):
    print("[Job] Running Monthly Budget Reminder Job...")
    conn = ai_engine.get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email, monthly_budget FROM users")
            users = cur.fetchall()
        for uid, uname, uemail, budget in users:
            if budget and float(budget) > 0:
                score = ai_engine.calculate_financial_health(
                    uid, datetime.now().year, datetime.now().month
                )
                body = (
                    f"Hello {uname} 📅,\n\n"
                    f"It's a new month! Your target budget is ₹{float(budget):,.0f}.\n"
                    f"Your previous financial health score was {score}/100. "
                    "Let's aim to beat it this month!\n\n"
                    "Best,\nFinora AI"
                )
                send_email(app, "Finora AI - Monthly Budget Start", uemail, body)
    finally:
        conn.close()


def mid_month_overspending_alert(app):
    print("[Job] Running Mid-Month Overspending Alert...")
    conn = ai_engine.get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email, monthly_budget FROM users")
            users = cur.fetchall()
            for uid, uname, uemail, budget in users:
                if not budget or float(budget) <= 0:
                    continue
                cur.execute(
                    "SELECT COALESCE(SUM(amount), 0) FROM expenses "
                    "WHERE user_id=%s AND expense_month=%s AND expense_year=%s",
                    (uid, datetime.now().month, datetime.now().year),
                )
                spent = float(cur.fetchone()[0] or 0)
                budget_f = float(budget)
                if spent > budget_f * 0.75:
                    pct = (spent / budget_f) * 100
                    body = (
                        f"🚨 ALERT: {uname}, you have used {pct:.0f}% of your budget "
                        f"(₹{spent:,.0f} of ₹{budget_f:,.0f}) and the month is only halfway through.\n\n"
                        "Please slow down on discretionary spending!\n\n"
                        "Best,\nFinora Alert System"
                    )
                    send_email(app, "⚠️ Overspending Alert!", uemail, body)
    finally:
        conn.close()


def init_email_system(app):
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")

    mail.init_app(app)

    scheduler = BackgroundScheduler()
    # Every Sunday at 9 AM
    scheduler.add_job(
        func=weekly_ai_report_job, args=[app],
        trigger="cron", day_of_week="sun", hour=9,
    )
    # 1st of every month at 8 AM
    scheduler.add_job(
        func=monthly_budget_reminder, args=[app],
        trigger="cron", day="1", hour=8,
    )
    # 15th of every month at 12 PM
    scheduler.add_job(
        func=mid_month_overspending_alert, args=[app],
        trigger="cron", day="15", hour=12,
    )

    scheduler.start()
    return scheduler