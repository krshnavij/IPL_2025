import streamlit as st
import pandas as pd
import io
import requests
from github import Github
import openpyxl
from datetime import datetime, date

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

# Placeholder for user login
if "user_name" not in st.session_state:
    st.session_state.user_name = None

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
    # Freeze the date input to today's date
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

                    # Extract the match time from the filtered data
                    match_time_str = filtered_data.loc[filtered_data["Fixture"] == fixture, "Time"].values[0]
                    match_datetime = datetime.strptime(f"{selected_date_str} {match_time_str}", "%d-%m-%Y %H:%M")
                    current_time = datetime.now()

                    # Check if the match time has passed to disable the submit button
                    is_disabled = current_time >= match_datetime

                    with st.form(f"fixture_selections_{i}", clear_on_submit=False):
                        if len(teams) == 2:
                            toss_winner_display = st.selectbox("Toss Winner:", abbreviated_teams, key=f"toss_{i}")
                            match_winner_display = st.selectbox("Match Winner:", abbreviated_teams, key=f"match_{i}")
                            submitted = st.form_submit_button("Submit Predictions", disabled=is_disabled)

                            if is_disabled:
                                st.warning(f"Match time has passed. Predictions for {fixture} are closed.")

                            if submitted:
                                if st.session_state.user_name not in predictions:
                                    predictions[st.session_state.user_name] = {}
                                predictions[st.session_state.user_name][fixture] = {
                                    "Toss": toss_winner_display,
                                    "Match Winner": match_winner_display,
                                    "Date": selected_date_str,
                                }
                                st.session_state.predictions = predictions

                                # Update Excel file automatically
                                try:
                                    g = Github(GITHUB_TOKEN)
                                    repo = g.get_repo(REPO_NAME)

                                    # Create user-specific file path
                                    user_file_path = f"predictions_{st.session_state.user_name.lower()}.xlsx"

                                    # Check if file exists
                                    try:
                                        file = repo.get_contents(user_file_path)
                                        excel_content = file.decoded_content
                                        excel_file = io.BytesIO(excel_content)
                                        existing_df = pd.read_excel(excel_file)
                                    except Exception:
                                        # If file does not exist, create an empty DataFrame
                                        existing_df = pd.DataFrame()

                                    # Prepare new predictions data
                                    new_data = []
                                    for match, prediction in predictions[
                                        st.session_state.user_name
                                    ].items():
                                        new_data.append(
                                            {
                                                "Date": prediction["Date"],
                                                "Match": match,
                                                "Toss": prediction["Toss"],
                                                "Match Winner": prediction["Match Winner"],
                                            }
                                        )
                                    new_df = pd.DataFrame(new_data)

                                    # Merge old and new data
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

                                    # Write updated data to Excel
                                    output = io.BytesIO()
                                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                                        updated_df.to_excel(writer, index=False)

                                    updated_excel_content = output.getvalue()

                                    # Update or create the file on GitHub
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

                                    st.success(
                                        "Prediction submitted!"
                                    )
                                except Exception as e:
                                    st.error(f"Error updating predictions: {e}")

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

                # Create a DataFrame with columns for User, Match, Toss Prediction, Match Prediction, and Date
                predictions_df = pd.DataFrame(all_predictions)
                predictions_df = predictions_df.set_index("Match")  # Set Match as index for better readability

                # Replace full team names with abbreviations in the Match, Toss Prediction, and Match Prediction columns
                def abbreviate_match(match):
                    teams = match.split(" vs ")
                    abbreviated_teams = [abbreviate_name(team) for team in teams]
                    return " vs ".join(abbreviated_teams)

                predictions_df.index = predictions_df.index.to_series().apply(abbreviate_match)
                predictions_df["Toss Prediction"] = predictions_df["Toss Prediction"].apply(abbreviate_name)
                predictions_df["Match Prediction"] = predictions_df["Match Prediction"].apply(abbreviate_name)

                # Display predictions
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
