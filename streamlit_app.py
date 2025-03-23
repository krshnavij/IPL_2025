import streamlit as st
import pandas as pd
import io
from github import Github
from datetime import datetime, date, timedelta

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
}


# Helper function to abbreviate team names
def abbreviate_name(name):
    return team_name_mapping.get(name.strip(), name.strip())


# GitHub configuration
DATA_URL = "https://raw.githubusercontent.com/krshnavij/IPL_2025/main/IPL_2025.csv"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = "krshnavij/IPL_2025"
SHARED_PREDICTIONS_FILE = "predictions.xlsx"

# Function to load shared predictions from GitHub
def load_shared_predictions():
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        file = repo.get_contents(SHARED_PREDICTIONS_FILE)
        excel_content = file.decoded_content
        excel_file = io.BytesIO(excel_content)
        predictions_df = pd.read_excel(excel_file)
        if predictions_df.empty:
            # Initialize with required columns if the file is empty
            predictions_df = pd.DataFrame(columns=["Date", "Match", "User", "Toss", "Match Winner", "Time"])
        return predictions_df
    except Exception:
        # Return an empty DataFrame with required columns if file does not exist
        return pd.DataFrame(columns=["Date", "Match", "User", "Toss", "Match Winner", "Time"])


# Function to save shared predictions to GitHub
def save_shared_predictions(predictions_df):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)

        try:
            file = repo.get_contents(SHARED_PREDICTIONS_FILE)
            excel_content = io.BytesIO()
            with pd.ExcelWriter(excel_content, engine="openpyxl") as writer:
                predictions_df.to_excel(writer, index=False)
            repo.update_file(SHARED_PREDICTIONS_FILE, "Update shared predictions", excel_content.getvalue(), file.sha)
        except Exception:
            # If file doesn't exist, create it
            excel_content = io.BytesIO()
            with pd.ExcelWriter(excel_content, engine="openpyxl") as writer:
                predictions_df.to_excel(writer, index=False)
            repo.create_file(SHARED_PREDICTIONS_FILE, "Create shared predictions file", excel_content.getvalue())
        return True
    except Exception as e:
        st.error(f"Error saving shared predictions: {e}")
        return False


# Function to load user-specific predictions from GitHub
def load_user_predictions(user_name):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        user_file_path = f"predictions_{user_name.lower()}.xlsx"
        file = repo.get_contents(user_file_path)
        excel_content = file.decoded_content
        excel_file = io.BytesIO(excel_content)
        predictions_df = pd.read_excel(excel_file)
        if predictions_df.empty:
            # Initialize with required columns if the file is empty
            predictions_df = pd.DataFrame(columns=["Date", "Match", "Toss", "Match Winner", "Time"])
        return predictions_df
    except Exception:
        # Return an empty DataFrame with required columns if file does not exist
        return pd.DataFrame(columns=["Date", "Match", "Toss", "Match Winner", "Time"])


# Function to save user-specific predictions to GitHub
def save_user_predictions(user_name, predictions_df):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        user_file_path = f"predictions_{user_name.lower()}.xlsx"

        try:
            file = repo.get_contents(user_file_path)
            excel_content = io.BytesIO()
            with pd.ExcelWriter(excel_content, engine="openpyxl") as writer:
                predictions_df.to_excel(writer, index=False)
            repo.update_file(user_file_path, "Update user predictions", excel_content.getvalue(), file.sha)
        except Exception:
            # If file doesn't exist, create it
            excel_content = io.BytesIO()
            with pd.ExcelWriter(excel_content, engine="openpyxl") as writer:
                predictions_df.to_excel(writer, index=False)
            repo.create_file(user_file_path, "Create user predictions file", excel_content.getvalue())
        return True
    except Exception as e:
        st.error(f"Error saving user predictions: {e}")
        return False


# Placeholder for user login
if "user_name" not in st.session_state:
    st.session_state.user_name = None

if st.session_state.user_name is None:  # Show login form
    username_input = st.text_input("Username:")
    password_input = st.text_input("Password:", type="password")
    if st.button("Login"):
        if username_input and password_input:
            for stored_username, stored_password in user_credentials.items():
                if stored_username.lower() == username_input.lower() and stored_password == password_input:
                    st.session_state.user_name = stored_username
                    st.rerun()
                    break
            else:
                st.error("Invalid username or password.")
        else:
            st.error("Please enter both username and password.")
    if st.checkbox("Forgot Password?"):
        forgot_username = st.text_input("Enter your username to reset password:")
        if st.button("Request Reset"):
            if forgot_username.lower() in [user.lower() for user in user_credentials]:
                st.success("Password reset request sent (placeholder). Check your email (not implemented).")
            else:
                st.error("Username not found.")
else:  # User is logged in, show the main app
    st.set_page_config(page_title="IPL PREDICTION COMPETITION", page_icon="📈")
    st.title("🏏 IPL PREDICTION 2025")

    # Freeze the date input to today's date
    selected_date = st.date_input(
        "Select a date to filter the data", value=date.today(), disabled=True
    )

    def parse_date(date_str):
        try:
            return pd.to_datetime(date_str, format="%d-%m-%Y")
        except ValueError:
            return pd.NaT

    try:
        data = pd.read_csv(DATA_URL)
        data["Date"] = data["Date"].str.strip()
        data["Date"] = data["Date"].apply(parse_date)
        data["Date"] = data["Date"].dt.date
        selected_date_datetime = pd.to_datetime(selected_date).date()
        filtered_data = data[data["Date"] == selected_date_datetime]

        filtered_data["Fixture"] = filtered_data["Fixture"].apply(
            lambda fixture: " vs ".join([abbreviate_name(team) for team in fixture.split(" vs ")])
        )

        if not filtered_data.empty:
            selected_date_str = pd.to_datetime(selected_date).strftime("%d-%m-%Y")
            st.text(f"Selected Date: {selected_date_str}")
            st.dataframe(filtered_data)
            fixtures_on_date = filtered_data["Fixture"].tolist()

            if "predictions" not in st.session_state:
                st.session_state.predictions = {}
            predictions = st.session_state.predictions

            shared_predictions_df = load_shared_predictions()  # Load shared predictions from GitHub
            user_predictions_df = load_user_predictions(st.session_state.user_name)  # Load user-specific predictions from GitHub

            for i, fixture in enumerate(fixtures_on_date):
                with st.container():
                    st.subheader(f"Fixture: {fixture}")
                    teams = fixture.split(" vs ")
                    abbreviated_teams = [abbreviate_name(team) for team in teams]

                    now = datetime.now()
                    ist_time = now + timedelta(hours=5, minutes=30)  # Convert to IST
                    submission_time_hour = ist_time.hour
                    submission_time_minute = ist_time.minute

                    # Determine if the submit button should be disabled based on the match timing
                    disable_submit = False
                    if len(fixtures_on_date) == 1:  # Only one match for the day
                        if submission_time_hour > 19 or (submission_time_hour == 19 and submission_time_minute >= 0):
                            disable_submit = True
                    else:
                        if i == 0 and (submission_time_hour > 15 or (submission_time_hour == 15 and submission_time_minute >= 0)):
                            disable_submit = True  # Disable for the 3:30 PM match after 3:00 PM
                        elif i == 1 and (submission_time_hour > 19 or (submission_time_hour == 19 and submission_time_minute >= 0)):
                            disable_submit = True  # Disable for the 7:30 PM match after 7:00 PM

                    with st.form(f"fixture_selections_{i}", clear_on_submit=False):
                        if len(teams) == 2:
                            toss_winner_display = st.selectbox("Toss Winner:", abbreviated_teams, key=f"toss_{i}")
                            match_winner_display = st.selectbox("Match Winner:", abbreviated_teams, key=f"match_{i}")
                            
                            # Conditionally enable or disable the submit button
                            submitted = st.form_submit_button("Submit Predictions", disabled=disable_submit)
                            
                            if disable_submit:
                                st.warning("Submission time for this match has exceeded the cutoff. Your prediction will not be recorded.")
                            elif submitted:
                                submission_time_ist = ist_time.strftime("%H:%M:%S")
                                selected_date_str = pd.to_datetime(selected_date).strftime("%d-%m-%Y")

                                # Update shared predictions file
                                existing_shared_index = shared_predictions_df[
                                    (shared_predictions_df["User"] == st.session_state.user_name) &
                                    (shared_predictions_df["Match"] == fixture) &
                                    (shared_predictions_df["Date"] == selected_date_str)
                                ].index

                                if not existing_shared_index.empty:
                                    shared_predictions_df.loc[existing_shared_index, ["Toss", "Match Winner", "Time"]] = [
                                        toss_winner_display, match_winner_display, submission_time_ist
                                    ]
                                else:
                                    new_shared_prediction = {
                                        "Date": selected_date_str,
                                        "Match": fixture,
                                        "User": st.session_state.user_name,
                                        "Toss": toss_winner_display,
                                        "Match Winner": match_winner_display,
                                        "Time": submission_time_ist,
                                    }
                                    shared_predictions_df = pd.concat([shared_predictions_df, pd.DataFrame([new_shared_prediction])], ignore_index=True)

                                save_shared_predictions(shared_predictions_df)

                                # Update user-specific predictions file
                                existing_user_index = user_predictions_df[
                                    (user_predictions_df["Match"] == fixture) &
                                    (user_predictions_df["Date"] == selected_date_str)
                                ].index

                                if not existing_user_index.empty:
                                    user_predictions_df.loc[existing_user_index, ["Toss", "Match Winner", "Time"]] = [
                                        toss_winner_display, match_winner_display, submission_time_ist
                                    ]
                                else:
                                    new_user_prediction = {
                                        "Date": selected_date_str,
                                        "Match": fixture,
                                        "Toss": toss_winner_display,
                                        "Match Winner": match_winner_display,
                                        "Time": submission_time_ist,
                                    }
                                    user_predictions_df = pd.concat([user_predictions_df, pd.DataFrame([new_user_prediction])], ignore_index=True)

                                save_user_predictions(st.session_state.user_name, user_predictions_df)

                                st.success("Prediction submitted!")

            # Display all predictions for the selected date across all users
            st.subheader(f"All Predictions for {selected_date_str} Across Users")
            shared_predictions_for_date = shared_predictions_df[shared_predictions_df["Date"] == selected_date_str]
            if not shared_predictions_for_date.empty:
                st.dataframe(shared_predictions_for_date)
            else:
                st.write("No predictions made for the selected date across users.")
    except FileNotFoundError:
        st.error("CSV file not found. Please make sure the URL is correct and the file exists.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

    if st.button("Logout"):
        st.session_state.user_name = None
        st.session_state.password_reset = None
        st.rerun()
