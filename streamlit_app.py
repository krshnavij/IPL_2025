import streamlit as st
import pandas as pd
import io
import requests
from github import Github
from datetime import datetime, date, time
import openpyxl

# Placeholder for user credentials
user_credentials = {
    "vijay": "nila",
    "nandini": "secret",
    "sanjay": "tvk",
    "mohan": "kumar",
    "ajay": "ruby",
    "madan": "maddy",
    "karunya": "balyam",
    "apoorva": "vasantha",
    "priya": "mythili",
    # Add more users if needed
}

# Team name abbreviations
team_name_mapping = {
    "Kolkata Knight Riders": "KKR",
    "Chennai Super Kings": "CSK",
    "Mumbai Indians": "MI",
    "Royal Challengers Bengaluru": "RCB",
    "Sunrisers Hyderabad": "SRH",
    "Delhi Capitals": "DC",
    "Punjab Kings": "PBKS",
    "Rajasthan Royals": "RR",
    "Lucknow Super Giants": "LSG",
    "Gujarat Titans": "GT",
    # Add other teams if needed
}

# Helper function to abbreviate team names
def abbreviate_name(name):
    return team_name_mapping.get(name.strip(), name.strip())

# Placeholder for password reset requests
password_reset_requests = {}

# --- AUTO LOGOUT FUNCTION ---
def check_auto_logout():
    # Define logout times
    logout_times = [time(10, 35), time(10, 40)]  # 3:00 PM and 5:00 PM
    
    # Get current time
    current_time = datetime.now().time()
    
    # Check if current time matches any logout time
    for logout_time in logout_times:
        if current_time >= logout_time and current_time < (logout_time.replace(minute=1)):  # Between logout_time and logout_time + 1 minute
            return True
    return False

# Placeholder for user login
if "user_name" not in st.session_state:
    st.session_state.user_name = None

# Check auto logout condition
if check_auto_logout():
    st.session_state.user_name = None
    st.warning("You have been logged out automatically due to the scheduled logout time.")
    st.stop()  # Stop further execution

if st.session_state.user_name is None:  # Show login form
    username_input = st.text_input("Username:")
    password_input = st.text_input("Password:", type="password")
    if st.button("Login"):
        if username_input and password_input:
            # Case-insensitive username check:
            for stored_username, stored_password in user_credentials.items():
                if stored_username.lower() == username_input.lower() and stored_password == password_input:
                    st.session_state.user_name = stored_username
                    st.rerun()
                    break
            else:
                st.error("Invalid username or password.")
        else:
            st.error("Please enter both username and password.")
    # Forgot Password
    if st.checkbox("Forgot Password?"):
        forgot_username = st.text_input("Enter your username to reset password:")
        if st.button("Request Reset"):
            if forgot_username.lower() in [user.lower() for user in user_credentials]:
                password_reset_requests[forgot_username.lower()] = True
                st.success("Password reset request sent (placeholder). Check your email (not implemented).")
            else:
                st.error("Username not found.")
elif "password_reset" in st.session_state and st.session_state.password_reset:
    new_password = st.text_input("New Password:", type="password")
    confirm_password = st.text_input("Confirm New Password:", type="password")
    if st.button("Change Password"):
        if new_password == confirm_password:
            user_credentials[st.session_state.user_name] = new_password
            st.success("Password changed successfully.")
            del st.session_state.password_reset
            st.rerun()
        else:
            st.error("Passwords do not match.")
else:  # User is logged in, show the main app
    # --- CONFIGS ---
    DATA_URL = "https://raw.githubusercontent.com/krshnavij/IPL_2025/main/IPL_2025.csv"
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]  # Fetch token from Streamlit Secrets
    REPO_NAME = "krshnavij/IPL_2025"  # Replace with your repo name

    # --- PAGE SETUP ---
    st.set_page_config(page_title="IPL PREDICTION COMPETITION", page_icon="📈")
    st.title("🏏 IPL PREDICTION 2025")

    # --- DATE INPUT ---
    selected_date = st.date_input(
        "Select a date to filter the data",
        value=date.today(),  # Default to today's date
        disabled=True  # Disable the user from selecting other dates
    )

    # --- DATE PARSING FUNCTION ---
    def parse_date(date_str):
        try:
            return pd.to_datetime(date_str, format="%d-%m-%Y")
        except ValueError:
            return pd.NaT

    # --- LOAD AND FILTER DATA ---
    try:
        data = pd.read_csv(DATA_URL)
        data["Date"] = data["Date"].str.strip()
        data["Date"] = data["Date"].apply(parse_date)
        data["Date"] = data["Date"].dt.date
        selected_date_datetime = pd.to_datetime(selected_date).date()
        filtered_data = data[data["Date"] == selected_date_datetime]
        if not filtered_data.empty:
            selected_date_str = pd.to_datetime(selected_date).strftime("%d-%m-%Y")
            st.text(f"Selected Date: {selected_date_str}")
            st.dataframe(filtered_data)
            fixtures_on_date = filtered_data["Fixture"].tolist()

            # --- PREDICTION LOGIC ---
            if "predictions" not in st.session_state:
                st.session_state.predictions = {}
            predictions = st.session_state.predictions

            for i, fixture in enumerate(fixtures_on_date):
                with st.container():
                    st.subheader(f"Fixture: {fixture}")
                    teams = fixture.split(" vs ")
                    abbreviated_teams = [abbreviate_name(team) for team in teams]  # Use abbreviations for dropdown

                    # Define match-specific cut-off times
                    cutoff_time_first_match = time(10, 35)  # 3:30 PM
                    cutoff_time_second_match = time(10, 40)  # 7:00 PM

                    # Get current time
                    current_time = datetime.now().time()

                    # Determine whether the button should be disabled
                    disable_button = False
                    if i == 0 and current_time >= cutoff_time_first_match:  # First match
                        disable_button = True
                    elif i == 1 and current_time >= cutoff_time_second_match:  # Second match
                        disable_button = True

                    # Prediction form
                    with st.form(f"fixture_selections_{i}", clear_on_submit=False):
                        if len(teams) == 2:
                            toss_winner_display = st.selectbox("Toss Winner:", abbreviated_teams, key=f"toss_{i}")
                            match_winner_display = st.selectbox("Match Winner:", abbreviated_teams, key=f"match_{i}")
                            submitted = st.form_submit_button("Submit Predictions", disabled=disable_button)
                            
                            if disable_button:
                                st.warning(f"Predictions for this match are closed.")
                            
                            if submitted:
                                if st.session_state.user_name not in predictions:
                                    predictions[st.session_state.user_name] = {}
                                predictions[st.session_state.user_name][fixture] = {
                                    "Toss": toss_winner_display,
                                    "Match Winner": match_winner_display,
                                    "Date": selected_date_str,
                                }
                                st.session_state.predictions = predictions
                                st.success("Prediction submitted!")

            # --- DISPLAY PREDICTIONS TABLE ---
            if predictions:
                st.subheader(f"Predictions for {selected_date_str}")
                all_predictions = []
                for user, user_predictions in predictions.items():
                    for match, prediction in user_predictions.items():
                        if prediction["Date"] == selected_date_str:  # Filter by selected date
                            all_predictions.append(
                                {
                                    "User": user,
                                    "Match": match,
                                    "Toss Prediction": prediction["Toss"],
                                    "Match Prediction": prediction["Match Winner"],
                                    "Date": prediction["Date"],
                                }
                            )

                predictions_df = pd.DataFrame(all_predictions)
                st.dataframe(predictions_df)
            else:
                st.write("No data available for the selected date.")
    except FileNotFoundError:
        st.error("CSV file not found. Please make sure the URL is correct and the file exists.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.write("Please check the data source, date format, and any other potential issues.")

    if st.button("Logout"):
        st.session_state.user_name = None
        st.session_state.password_reset = None
        st.rerun()
