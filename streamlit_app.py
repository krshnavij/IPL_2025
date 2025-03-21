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

# Placeholder for password reset requests
password_reset_requests = {}

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
                password_reset_requests[forgot_username.lower()] = True
                st.success("Password reset request sent (placeholder). Check your email (not implemented).")
            else:
                st.error("Username not found.")
else:  # User is logged in, show the main app
    DATA_URL = "https://raw.githubusercontent.com/krshnavij/IPL_2025/main/IPL_2025.csv"
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = "krshnavij/IPL_2025"

    st.set_page_config(page_title="IPL PREDICTION COMPETITION", page_icon="📈")
    st.title("🏏 IPL PREDICTION 2025")

    # Freeze the date input to today's date
    selected_date = st.date_input(
        "Select a date to filter the data",
        value=date.today(),
        disabled=True
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
                        # Disable for the 7:30 PM match after 7:00 PM
                        if submission_time_hour > 19 or (submission_time_hour == 19 and submission_time_minute >= 0):
                            disable_submit = True
                    else:
                        # Multiple matches for the day
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

                                # Update predictions only if submission is valid
                                if st.session_state.user_name not in predictions:
                                    predictions[st.session_state.user_name] = {}
                                predictions[st.session_state.user_name][fixture] = {
                                    "Toss": toss_winner_display,
                                    "Match Winner": match_winner_display,
                                    "Date": selected_date_str,
                                    "Time": submission_time_ist,
                                }
                                st.session_state.predictions = predictions

                                # Save predictions to GitHub
                                try:
                                    g = Github(GITHUB_TOKEN)
                                    repo = g.get_repo(REPO_NAME)

                                    user_file_path = f"predictions_{st.session_state.user_name.lower()}.xlsx"

                                    try:
                                        file = repo.get_contents(user_file_path)
                                        excel_content = file.decoded_content
                                        excel_file = io.BytesIO(excel_content)
                                        existing_df = pd.read_excel(excel_file)
                                    except Exception:
                                        existing_df = pd.DataFrame()

                                    new_data = []
                                    for match, prediction in predictions[st.session_state.user_name].items():
                                        new_data.append(
                                            {
                                                "Date": prediction["Date"],
                                                "Match": match,
                                                "Toss": prediction["Toss"],
                                                "Match Winner": prediction["Match Winner"],
                                                "Time": prediction["Time"],
                                            }
                                        )
                                    new_df = pd.DataFrame(new_data)

                                    if not existing_df.empty:
                                        merged_df = pd.concat(
                                            [existing_df, new_df], ignore_index=True
                                        )
                                        merged_df = merged_df.drop_duplicates(
                                            subset=["Match", "Date"], keep="last"
                                        )
                                        updated_df = merged_df
                                    else:
                                        updated_df = new_df

                                    output = io.BytesIO()
                                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                                        updated_df.to_excel(writer, index=False)

                                    updated_excel_content = output.getvalue()

                                    try:
                                        repo.update_file(
                                            user_file_path,
                                            "Update predictions",
                                            updated_excel_content,
                                            file.sha,
                                        )
                                    except Exception:
                                        repo.create_file(
                                            user_file_path,
                                            "Create predictions file",
                                            updated_excel_content,
                                        )

                                    st.success("Prediction submitted!")
                                except Exception as e:
                                    st.error(f"Error updating predictions: {e}")

            if predictions:
                st.subheader(f"Predictions for {selected_date_str}")
                all_predictions = []
                for user, user_predictions in predictions.items():
                    for match, prediction in user_predictions.items():
                        if prediction["Date"] == selected_date_str:
                            abbreviated_match = " vs ".join([abbreviate_name(team) for team in match.split(" vs ")])
                            all_predictions.append(
                                {
                                    "User": user,
                                    "Match": abbreviated_match,
                                    "Toss Prediction": prediction["Toss"],
                                    "Match Prediction": prediction["Match Winner"],
                                    "Date": prediction["Date"],
                                    "Time": prediction["Time"],
                                }
                            )

                predictions_df = pd.DataFrame(all_predictions)
                st.dataframe(predictions_df)  # Display interactive table
            else:
                st.write("No data available for the selected date.")
    except FileNotFoundError:
        st.error("CSV file not found. Please make sure the URL is correct and the file exists.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

    if st.button("Logout"):
        st.session_state.user_name = None
        st.session_state.password_reset = None
        st.rerun()
