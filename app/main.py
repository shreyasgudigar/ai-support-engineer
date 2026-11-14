from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field

from app.auth.routes import router as auth_router
from app.auth.dependencies import get_current_user, require_roles
from app.agents.support_agent import run_support_agent

from app.db import (
    get_all_tickets,
    get_tickets_by_customer,
    get_ticket_by_id,
    create_ticket,
    save_ai_result,
    approve_ai_answer,
    edit_and_approve_answer,
    reject_ai_answer,
)

from app.predictor import predict_intent
from app.predictor_v2 import predict_intent_v2
from app.retriever import search_knowledge
from app.generator import generate_support_answer


# --------------------------------------------------
# APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="AI Customer Support System",
    description="AI-powered customer support with authentication and human review",
    version="1.2.0",
)

app.include_router(auth_router)


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class PredictionRequest(BaseModel):
    message: str = Field(min_length=1)


class PredictionRequestV2(BaseModel):
    message: str = Field(min_length=1)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class TicketRequest(BaseModel):
    message: str = Field(min_length=1)


class SupportAnswerRequest(BaseModel):
    question: str = Field(min_length=1)


class SupportProcessRequest(BaseModel):
    ticket_id: int = Field(gt=0)


class ReviewAnswerRequest(BaseModel):
    reviewed_answer: str = Field(min_length=1)


# --------------------------------------------------
# ROLE DEPENDENCIES
# --------------------------------------------------

staff_required = Depends(
    require_roles("support_agent", "admin")
)


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "AI Customer Support API is running"
    }


# --------------------------------------------------
# TICKET MANAGEMENT
# --------------------------------------------------

@app.get("/tickets")
def get_tickets(
    current_user=Depends(get_current_user),
):
    role = current_user["role"]

    if role == "customer":
        return get_tickets_by_customer(
            current_user["customer_id"]
        )

    if role in ["support_agent", "admin"]:
        return get_all_tickets()

    raise HTTPException(
        status_code=403,
        detail="You do not have permission to view tickets",
    )


@app.post("/tickets", status_code=201)
def submit_ticket(
    request: TicketRequest,
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "customer":
        raise HTTPException(
            status_code=403,
            detail="Only customers can create support tickets",
        )

    customer_id = current_user["customer_id"]

    prediction = predict_intent(request.message)

    ticket = create_ticket(
        customer_id=customer_id,
        message=request.message,
        category=prediction["predicted_category"],
        confidence=prediction["confidence"],
    )

    return ticket


# --------------------------------------------------
# INTENT CLASSIFICATION
# --------------------------------------------------

@app.post("/predict")
def predict(
    request: PredictionRequest,
    current_user=staff_required,
):
    return predict_intent(request.message)


@app.post("/predict/v2")
def predict_v2(
    request: PredictionRequestV2,
    current_user=staff_required,
):
    return predict_intent_v2(request.message)


# --------------------------------------------------
# KNOWLEDGE BASE SEARCH
# --------------------------------------------------

@app.post("/knowledge/search")
def knowledge_search(
    request: KnowledgeSearchRequest,
    current_user=staff_required,
):
    results = search_knowledge(
        query=request.query,
        top_k=request.top_k,
    )

    return {
        "query": request.query,
        "total_results": len(results),
        "results": results,
    }


# --------------------------------------------------
# AI SUPPORT ANSWER GENERATION
# --------------------------------------------------

@app.post("/support/process")
def process_support(
    request: SupportProcessRequest,
    current_user=staff_required,
):
    # Step 1: Fetch the original ticket
    ticket = get_ticket_by_id(request.ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    # Step 2: Run the AI agent
    agent_result = run_support_agent(ticket["message"])

    # Step 3: Save the generated answer
    saved_ticket = save_ai_result(
        ticket_id=request.ticket_id,
        generated_answer=agent_result["answer"],
        review_status=agent_result["review_status"],
    )

    if saved_ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket could not be updated",
        )

    # Step 4: Return the agent's complete decision
    return {
        "ticket_id": saved_ticket["id"],
        **agent_result,
        "review_status": saved_ticket["review_status"],
    }

# --------------------------------------------------
# HUMAN REVIEW: APPROVE
# --------------------------------------------------

@app.post("/tickets/{ticket_id}/approve")
def approve_answer(
    ticket_id: int,
    current_user=staff_required,
):
    result = approve_ai_answer(ticket_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found or not pending review",
        )

    return {
        "message": "AI answer approved successfully",
        "ticket": result,
    }


# --------------------------------------------------
# HUMAN REVIEW: EDIT AND APPROVE
# --------------------------------------------------

@app.post("/tickets/{ticket_id}/edit-approve")
def edit_approve_answer(
    ticket_id: int,
    request: ReviewAnswerRequest,
    current_user=staff_required,
):
    result = edit_and_approve_answer(
        ticket_id=ticket_id,
        reviewed_answer=request.reviewed_answer,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found or not pending review",
        )

    return {
        "message": "Edited answer approved successfully",
        "ticket": result,
    }


# --------------------------------------------------
# HUMAN REVIEW: REJECT
# --------------------------------------------------

@app.post("/tickets/{ticket_id}/reject")
def reject_answer(
    ticket_id: int,
    current_user=staff_required,
):
    result = reject_ai_answer(ticket_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found or not pending review",
        )

    return {
        "message": "AI answer rejected successfully",
        "ticket": result,
    }