import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Employee Salary Tracker", page_icon="👨‍💼", layout="wide")

def parse_hours(value):
    """Convert HH:MM string to decimal hours"""
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        value = str(value).strip()
        if ":" in value:
            h, m = value.split(":")
            return int(h) + int(m) / 60
        return float(value)
    except:
        return 0.0


def calculate_salary(df, basic_salary, allowance, holidays=[]):
    # Ensure datetime parsing
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["In time"] = pd.to_datetime(df["In time"], errors="coerce").dt.time
    df["Out time"] = pd.to_datetime(df["Out time"], errors="coerce").dt.time

    # Wage calculations
    daily_wage = (basic_salary + allowance) * 12 / 365
    hourly_wage = daily_wage / 8

    results = []
    for _, row in df.iterrows():
        emp_id = row["Employee ID"]
        emp_name = row["Employee Name"]
        date = row["Date"]

        total_hours = parse_hours(row.get("Total Working hours", 0))
        extra_hours = parse_hours(row.get("Extra Working Time", 0))


        # Apply Friday/holiday multiplier
        multiplier = 1
        if date.weekday() == 4 or date.date() in holidays:  # Friday=4
            multiplier = 1.5

        normal_pay = total_hours * hourly_wage * multiplier
        extra_pay = extra_hours * hourly_wage
        total_pay = normal_pay + extra_pay

        results.append({
            "Employee ID": emp_id,
            "Employee Name": emp_name,
            "Date": date.date(),
            "In Time": row["In time"],
            "Out Time": row["Out time"],
            "Total Hours": total_hours,
            "Extra Hours": extra_hours,
            "Daily Pay": round(total_pay, 2)
        })

    breakdown_df = pd.DataFrame(results)

    # Monthly totals
    monthly_totals = breakdown_df.groupby(["Employee ID", "Employee Name"]).agg({
        "Total Hours": "sum",
        "Extra Hours": "sum",
        "Daily Pay": "sum"
    }).reset_index()

    # Add fixed monthly salary (basic + allowance)
    monthly_totals["Fixed Monthly Pay"] = basic_salary + allowance

    # Add final salary = fixed salary + calculated daily pay
    monthly_totals["Final Monthly Pay"] = monthly_totals["Daily Pay"] + (basic_salary + allowance)

    return breakdown_df, monthly_totals, hourly_wage, daily_wage


def main():
    st.title("👨‍💼 Employee Salary Tracker")

    uploaded_file = st.file_uploader("Upload Employee Attendance File (XLSX)", type=["xlsx"])
    basic_salary = st.number_input("Enter Basic Monthly Salary (INR)", min_value=0, step=1000)
    allowance = st.number_input("Enter Monthly Allowance (INR)", min_value=0, step=500)

    if uploaded_file and basic_salary > 0:
        df = pd.read_excel(uploaded_file)

        # Optional: holiday list
        holidays_input = st.text_area("Enter Holidays (comma-separated YYYY-MM-DD)", "")
        holidays = []
        if holidays_input:
            holidays = [datetime.date.fromisoformat(d.strip()) for d in holidays_input.split(",") if d.strip()]

        breakdown_df, monthly_totals, hourly_wage, daily_wage = calculate_salary(df, basic_salary, allowance, holidays)

        st.subheader("📊 Daily Breakdown")
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

        st.subheader("📑 Monthly Totals per Employee")
        st.dataframe(monthly_totals, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Hourly Wage", f"₹ {hourly_wage:,.2f}")
        with col2:
            st.metric("Daily Wage", f"₹ {daily_wage:,.2f}")

        # Chart: Salary per employee
        fig = px.bar(monthly_totals, x="Employee Name", y="Daily Pay", title="Salary Earned per Employee", text="Daily Pay")
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()

