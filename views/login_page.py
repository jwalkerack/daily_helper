import os
import streamlit as st

from services.auth_service import authenticate_user, load_approved_users
from services.logging_service import logger


def render_login_page():
    logger.info("Rendering login page.")

    st.title("Daily Helper")
    st.subheader("Log in")

    st.write("Please log in using the email address and access code provided by your consultant.")

    email = st.text_input("Email address")
    access_code = st.text_input("Access code", type="password")

    if os.getenv("APP_ENV") == "development":
        with st.expander("Debug login setup"):
            st.caption("Use this while developing only. Remove or hide before real users.")
            users = load_approved_users()
            st.write(f"Approved users loaded: {len(users)}")

            if users:
                st.write("Configured users:")
                for user in users:
                    st.write(
                        {
                            "user_id": user.get("user_id"),
                            "email": user.get("email"),
                            "role": user.get("role"),
                            "active": user.get("active"),
                        }
                    )

    if st.button("Log in", type="primary"):
        logger.info("Login button clicked.")

        user = authenticate_user(email, access_code)

        if user is None:
            logger.warning(f"Login failed in UI for email input: {email}")
            st.error("Login failed. Please check your email address and access code.")
            return

        st.session_state["user"] = user
        logger.info(f"User stored in session_state: {user}")
        st.success("Logged in successfully.")
        st.rerun()