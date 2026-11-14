
import os
import streamlit as st
import requests

# =========================================================
# CONFIGURATION
# =========================================================

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

API_SESSION = requests.Session()
API_SESSION.trust_env = False

REQUEST_TIMEOUT = 120

st.set_page_config(
    page_title="AI Customer Support",
    page_icon="🤖",
    layout="wide"
)

# =========================================================
# SESSION STATE
# =========================================================

DEFAULT_STATE = {
    "token": None,
    "user": None,
    "selected_ticket": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# API HELPER
# =========================================================

def api_request(method, endpoint, **kwargs):
    headers = kwargs.pop("headers", {}).copy()

    if st.session_state.token:
        headers["Authorization"] = (
            f"Bearer {st.session_state.token}"
        )

    try:
        response = API_SESSION.request(
            method=method,
            url=f"{API_URL}{endpoint}",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            **kwargs
        )

        if response.status_code == 401:
            st.session_state.token = None
            st.session_state.user = None
            st.error("Your session has expired. Please log in again.")
            st.stop()

        if response.status_code >= 400:
            try:
                detail = response.json().get(
                    "detail",
                    response.text
                )
            except ValueError:
                detail = response.text

            st.error(
                f"API error ({response.status_code}): {detail}"
            )
            return None

        if response.status_code == 204:
            return {}

        return response.json()

    except requests.Timeout:
        st.error(
            "The API request timed out. "
            "Check that FastAPI is running and try again."
        )
        return None

    except requests.RequestException as exc:
        st.error(f"Could not connect to FastAPI: {exc}")
        return None

    except ValueError:
        st.error("The API returned an invalid response.")
        return None


# =========================================================
# LOGIN
# =========================================================

def login():
    st.title("🤖 AI Customer Support Dashboard")
    st.caption(
        "ML Intent Classification · RAG · LLM · Human Review"
    )

    st.divider()
    st.subheader("Staff Login")

    with st.form("login_form"):
        email = st.text_input(
            "Email",
            placeholder="Enter staff email"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Login",
            type="primary",
            use_container_width=True
        )

    if not submitted:
        return

    if not email.strip() or not password:
        st.error("Enter both email and password.")
        return

    try:
        with st.spinner("Connecting to support system..."):
            response = API_SESSION.post(
                f"{API_URL}/auth/login",
                data={
                    "username": email.strip(),
                    "password": password
                },
                timeout=REQUEST_TIMEOUT
            )

        if response.status_code != 200:
            try:
                detail = response.json().get(
                    "detail",
                    "Check your email and password."
                )
            except ValueError:
                detail = "Check your email and password."

            st.error(
                f"Login failed ({response.status_code}): {detail}"
            )
            return

        result = response.json()
        user = result.get("user", {})
        token = result.get("access_token")

        if not token:
            st.error("Login response did not contain an access token.")
            return

        if user.get("role") not in ["support_agent", "admin"]:
            st.error(
                "Access denied. Please use a staff account."
            )
            return

        st.session_state.token = token
        st.session_state.user = user
        st.session_state.selected_ticket = None

        st.rerun()

    except requests.Timeout:
        st.error(
            "Login timed out. Check the FastAPI terminal "
            "for errors and confirm the API is running."
        )

    except requests.RequestException as exc:
        st.error(f"API connection failed: {exc}")

    except ValueError:
        st.error("The API returned an invalid login response.")


# =========================================================
# LOGOUT
# =========================================================

def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.selected_ticket = None

    for key in list(st.session_state.keys()):
        if key.startswith("result_") or key.startswith("answer_"):
            del st.session_state[key]

    st.rerun()


# =========================================================
# TICKET STATUS HELPERS
# =========================================================

def get_review_status(ticket):
    return ticket.get("review_status") or "not processed"


def clear_ticket_result(ticket_id):
    st.session_state.pop(
        f"result_{ticket_id}",
        None
    )

    st.session_state.pop(
        f"answer_{ticket_id}",
        None
    )


# =========================================================
# MAIN DASHBOARD
# =========================================================

def dashboard():

    # HEADER
    col1, col2 = st.columns([5, 1])

    with col1:
        st.title("🤖 AI Customer Support")
        st.caption(
            "ML Intent Classification · RAG · LLM · Human Review"
        )

    with col2:
        if st.button(
            "Logout",
            use_container_width=True
        ):
            logout()

    user = st.session_state.user or {}

    st.success(
        f"Logged in as {user.get('email', 'Staff')} "
        f"({user.get('role', 'staff')})"
    )

    st.divider()

    # -----------------------------------------------------
    # LOAD TICKETS
    # -----------------------------------------------------

    st.subheader("Support Tickets")

    refresh_col, info_col = st.columns([1, 4])

    with refresh_col:
        if st.button("🔄 Refresh Tickets"):
            st.rerun()

    with info_col:
        st.caption(
            "Select a ticket to run the AI support workflow "
            "and review its generated answer."
        )

    tickets = api_request(
        "GET",
        "/tickets"
    )

    if tickets is None:
        st.warning("Could not load tickets.")
        return

    if not isinstance(tickets, list):
        st.error("Unexpected ticket response from the API.")
        return

    if not tickets:
        st.info("No support tickets found.")
        return

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    total = len(tickets)

    pending = sum(
        get_review_status(ticket) == "pending"
        for ticket in tickets
    )

    approved = sum(
        get_review_status(ticket) == "approved"
        for ticket in tickets
    )

    rejected = sum(
        get_review_status(ticket) == "rejected"
        for ticket in tickets
    )

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Total Tickets", total)
    m2.metric("Pending Review", pending)
    m3.metric("Approved", approved)
    m4.metric("Rejected", rejected)

    st.divider()

    # -----------------------------------------------------
    # TICKET LIST
    # -----------------------------------------------------

    st.subheader("Ticket Queue")

    for ticket in tickets:

        ticket_id = ticket.get("id")

        if ticket_id is None:
            continue

        status = get_review_status(ticket)

        with st.container(border=True):

            left, right = st.columns([5, 1])

            with left:
                st.markdown(f"**Ticket #{ticket_id}**")

                st.write(
                    ticket.get("message", "No message available.")
                )

                category = (
                    ticket.get("category")
                    or ticket.get("predicted_category")
                    or "Unknown"
                )
                st.caption(
                    f"Category: {category} "
                    f"| Review status: {status}"
                )

            with right:
                if st.button(
                    "Open",
                    key=f"open_{ticket_id}",
                    use_container_width=True
                ):
                    st.session_state.selected_ticket = ticket_id
                    st.rerun()

    # -----------------------------------------------------
    # SELECTED TICKET
    # -----------------------------------------------------

    selected_id = st.session_state.selected_ticket

    if selected_id is None:
        st.info(
            "Select a ticket using its Open button "
            "to view and process it."
        )
        return

    selected_ticket = next(
        (
            ticket for ticket in tickets
            if ticket.get("id") == selected_id
        ),
        None
    )

    if selected_ticket is None:
        st.warning("The selected ticket is no longer available.")
        st.session_state.selected_ticket = None
        return

    st.divider()

    st.header(f"Ticket #{selected_id}")

    st.write(selected_ticket.get("message", ""))

    status = get_review_status(selected_ticket)

    st.caption(f"Current review status: {status}")

    # -----------------------------------------------------
    # RUN AI SUPPORT AGENT
    # -----------------------------------------------------

    run_col, rerun_col = st.columns([3, 1])

    with run_col:
        run_label = (
            "🔄 Rerun AI Support Agent"
            if status in ["approved", "rejected"]
            else "🚀 Run AI Support Agent"
        )

        if st.button(
            run_label,
            type="primary",
            use_container_width=True
        ):
            with st.spinner(
                "Running intent classification, "
                "knowledge retrieval and answer generation..."
            ):
                result = api_request(
                    "POST",
                    "/support/process",
                    json={
                        "ticket_id": selected_id
                    }
                )

            if result:
                st.session_state[
                    f"result_{selected_id}"
                ] = result
                st.rerun()

    if status in ["approved", "rejected"]:
        st.info(
            f"ℹ️ This ticket is already **{status}**. "
            "Click 'Rerun AI Support Agent' above to generate a new answer."
        )

    # -----------------------------------------------------
    # DISPLAY AI RESULTS
    # -----------------------------------------------------

    result = st.session_state.get(
        f"result_{selected_id}"
    )

    if not result:
        return

    # Check if the result has already been reviewed or if review is pending
    current_result_status = result.get("review_status", status)

    st.divider()
    st.subheader("AI Agent Results")

    # INTENT AND ROUTING
    intent = result.get("intent", {})

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Predicted Intent",
        intent.get("category", "Unknown")
    )

    confidence = intent.get("confidence")

    c2.metric(
        "Confidence",
        f"{confidence:.2%}" if isinstance(confidence, (int, float))
        else "N/A"
    )

    c3.metric(
        "Routing Decision",
        result.get("routing_status", "Unknown")
    )

    if intent.get("margin") is not None:
        st.caption(
            f"Classification margin: {intent['margin']:.4f} "
            f"| Model version: {intent.get('model_version', 'Unknown')}"
        )

    if result.get("review_reasons"):
        st.warning(
            "Review reasons: "
            + ", ".join(result["review_reasons"])
        )

    # -----------------------------------------------------
    # KNOWLEDGE SOURCES
    # -----------------------------------------------------

    st.subheader("Retrieved Knowledge Sources")

    sources = result.get("sources", [])

    if sources:
        for source in sources:
            similarity = source.get("similarity", 0)

            st.markdown(
                f"**{source.get('title', 'Untitled')}**  \n"
                f"Similarity: {similarity:.4f}"
            )
    else:
        st.warning(
            "No sufficiently relevant knowledge sources were found. "
            "The generated answer may use the fallback response."
        )

    # -----------------------------------------------------
    # GENERATED ANSWER
    # -----------------------------------------------------

    st.subheader("Generated Support Answer")

    answer_key = f"answer_{selected_id}"

    if answer_key not in st.session_state:
        st.session_state[answer_key] = result.get("answer", "")

    edited_answer = st.text_area(
        "Review or edit the answer before approval",
        height=180,
        key=answer_key
    )

    st.caption(
        f"Human review required: "
        f"{result.get('needs_review', True)}"
    )

    # -----------------------------------------------------
    # HUMAN REVIEW ACTIONS
    # -----------------------------------------------------

    if current_result_status not in ["pending"]:
        st.info(
            f"ℹ️ Review is already finalized for this ticket (Status: **{current_result_status}**). "
            "To submit a new review, click 'Rerun AI Support Agent' first."
        )
    else:
        st.subheader("Human Review")

        approve_col, edit_col, reject_col = st.columns(3)

        # APPROVE
        with approve_col:

            if st.button(
                "✅ Approve",
                key=f"approve_{selected_id}",
                use_container_width=True
            ):

                response = api_request(
                    "POST",
                    f"/tickets/{selected_id}/approve"
                )

                if response:
                    st.success(
                        response.get("message", "Answer approved.")
                    )

                    clear_ticket_result(selected_id)
                    st.rerun()

        # EDIT AND APPROVE
        with edit_col:

            if st.button(
                "✏️ Edit and Approve",
                key=f"edit_{selected_id}",
                use_container_width=True
            ):

                if not edited_answer.strip():
                    st.error("The answer cannot be empty.")

                else:
                    response = api_request(
                        "POST",
                        f"/tickets/{selected_id}/edit-approve",
                        json={
                            "reviewed_answer": edited_answer.strip()
                        }
                    )

                    if response:
                        st.success(
                            response.get(
                                "message",
                                "Edited answer approved."
                            )
                        )

                        clear_ticket_result(selected_id)
                        st.rerun()

        # REJECT
        with reject_col:

            if st.button(
                "❌ Reject",
                key=f"reject_{selected_id}",
                use_container_width=True
            ):

                response = api_request(
                    "POST",
                    f"/tickets/{selected_id}/reject"
                )

                if response:
                    st.success(
                        response.get("message", "Answer rejected.")
                    )

                    clear_ticket_result(selected_id)
                    st.rerun()


# =========================================================
# APPLICATION ENTRY POINT
# =========================================================

if not st.session_state.token:
    login()
else:
    dashboard()
