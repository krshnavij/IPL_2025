import streamlit as st
import pandas as pd

# Placeholder for user credentials (REPLACE with your actual database or authentication)
user_credentials = {
    "vijay": "password",
    "nandini": "secret",
    "VIJAY": "password",  # Example of case variation
    # ... more users
}

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
                    st.session_state.user_name = stored_username  # Store the correct case
                    st.rerun()
                    break  # Exit the loop once a match is found
            else:  # This else is associated with the for loop
                st.error("Invalid username or password.")

        else:
            st.error("Please enter both username and password.")

    # Forgot Password
    if st.checkbox("Forgot Password?"):
        forgot_username = st.text_input("Enter your username to reset password:")
        if st.button("Request Reset"):
            if forgot_username.lower() in [user.lower() for user in user_credentials]:  # Case insensitive check
                # In a real app, you would generate a unique reset token,
                # send an email to the user with the token and a reset link.
                password_reset_requests[forgot_username.lower()] = True  # Placeholder, use lower case for consistency.
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

    # --- PAGE SETUP ---
    st.set_page_config(page_title="IPL PREDICTION COMPETITION", page_icon="📈")
    st.title("🏏 IPL PREDICTION 2025")

    # --- DATE INPUT ---
    selected_date = st.date_input("Select a date to filter the data")

    # --- DATE PARSING FUNCTION ---
    def parse_date(date_str):
        try:
            return pd.to_datetime(date_str, format="%d-%m-%Y")
        except ValueError:
            return pd.NaT

    # --- LOAD AND FILTER DATA ---
    try:
        data = pd.read_csv(DATA_URL)
        data['Date'] = data['Date'].str.strip()
        data['Date'] = data['Date'].apply(parse_date)
        data['Date'] = data['Date'].dt.date

        selected_date_datetime = pd.to_datetime(selected_date).date()
        filtered_data = data[data['Date'] == selected_date_datetime]

        if not filtered_data.empty:
            selected_date_str = pd.to_datetime(selected_date).strftime("%d-%m-%Y")
            st.text(f"Selected Date: {selected_date_str}")

            st.dataframe(filtered_data)

            fixtures_on_date = filtered_data['Fixture'].tolist()

            # --- PREDICTION LOGIC ---
            if "predictions" not in st.session_state:
                st.session_state.predictions = {}  # Dictionary to store predictions
            predictions = st.session_state.predictions

            for i, fixture in enumerate(fixtures_on_date):
                with st.container():  # Use a container for each fixture
                    st.subheader(f"Fixture: {fixture}")  # Display fixture name as a subheader

                    with st.form(f"fixture_selections_{i}", clear_on_submit=False):  # Single form per fixture
                        teams = fixture.split(" vs ")
                        if len(teams) == 2:
                            toss_winner_options = teams
                            match_winner_options = teams

                            col1, col2 = st.columns(2)  # Columns for toss and match in the *same* form

                            with col1:
                                # Abbreviate team names for display in the dropdown (first letters)
                                toss_winner_options_display = ["".join(word[0] for word in team.split()) for team in toss_winner_options]
                                toss_winner_display = st.selectbox("Toss Winner:", toss_winner_options_display)

                                # Get the original team name based on the displayed selection
                                toss_winner = toss_winner_options[toss_winner_options_display.index(toss_winner_display)]

                            with col2:
                                # Abbreviate team names for display in the dropdown (first letters)
                                match_winner_options_display = ["".join(word[0] for word in team.split()) for team in match_winner_options]
                                match_winner_display = st.selectbox("Match Winner:", match_winner_options_display)

                                # Get the original team name based on the displayed selection
                                match_winner = match_winner_options[match_winner_options_display.index(match_winner_display)]

                            submitted = st.form_submit_button("Submit Predictions")  # Single submit button

                        if submitted:  # Handle submission for the entire fixture
                            # Store predictions by user and match
                            if st.session_state.user_name not in predictions:
                                predictions[st.session_state.user_name] = {}

                            predictions[st.session_state.user_name][fixture] = {
                                "Toss": toss_winner,
                                "Match Winner": match_winner
                            }

                            st.session_state.predictions = predictions
                            st.rerun()  # Important: Rerun to update the predictions table

                    st.write("---")

            # --- DISPLAY PREDICTIONS TABLE ---
            if predictions:
                # Filter predictions based on selected date
                predictions_for_date = {}
                for user, user_predictions in predictions.items():
                    for match, prediction in user_predictions.items():
                        # Check if the match is on the selected date
                        match_date_row = data[data['Fixture'] == match]['Date'].iloc[0] if not data[data['Fixture'] == match].empty else None
                        if match_date_row == selected_date_datetime:
                            if user not in predictions_for_date:
                                predictions_for_date[user] = {}
                            predictions_for_date[user][match] = prediction

                if predictions_for_date:  # Check if there are any predictions for the selected date
                    all_predictions = []
                    for user, user_predictions in predictions_for_date.items():
                        for match, prediction in user_predictions.items():
                            all_predictions.append({
                                "Match": match,
                                user: f"Toss: {''.join(word[0] for word in prediction['Toss'].split())} & Match: {''.join(word[0] for word in prediction['Match Winner'].split())}"
                            })

                    predictions_df = pd.DataFrame(all_predictions)
                    predictions_df = predictions_df.set_index("Match")
                    predictions_df = predictions_df.pivot_table(index="Match", columns=None, aggfunc='first').fillna("")

                    st.subheader("All Predictions")
                    st.dataframe(predictions_df)
                else:
                    st.write("No predictions yet for this date.") # More specific message

            else:
                st.write("No predictions yet.")

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