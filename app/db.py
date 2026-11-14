import os
import psycopg

from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()


def get_connection():
    connection = psycopg.connect(
        os.getenv("DATABASE_URL"),
        row_factory=dict_row
    )

    return connection


def get_all_tickets():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM support_tickets ORDER BY id"
            )

            tickets = cursor.fetchall()

    return tickets

def create_ticket(customer_id: int, message: str, category: str, confidence: float):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO support_tickets
                    (customer_id, message, predicted_category, confidence)
                VALUES (%s, %s, %s, %s)
                RETURNING id, customer_id, message,
                          predicted_category, confidence, status;
                """,
                (customer_id, message, category, confidence),
            )
            ticket = cursor.fetchone()

    return ticket


def save_ai_result(ticket_id: int, generated_answer: str, review_status: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE support_tickets
                SET generated_answer = %s,
                    review_status = %s
                WHERE id = %s
                RETURNING id, generated_answer, review_status;
                """,
                (generated_answer, review_status, ticket_id),
            )

            ticket = cursor.fetchone()

    return ticket

def approve_ai_answer(ticket_id: int):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE support_tickets
                SET reviewed_answer = generated_answer,
                    review_status = 'approved',
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND review_status = 'pending'
                  AND generated_answer IS NOT NULL
                RETURNING id, reviewed_answer, review_status, reviewed_at;
                """,
                (ticket_id,),
            )
            return cursor.fetchone()


def edit_and_approve_answer(ticket_id: int, reviewed_answer: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE support_tickets
                SET reviewed_answer = %s,
                    review_status = 'approved',
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND review_status = 'pending'
                  AND generated_answer IS NOT NULL
                RETURNING id, reviewed_answer, review_status, reviewed_at;
                """,
                (reviewed_answer, ticket_id),
            )
            return cursor.fetchone()


def reject_ai_answer(ticket_id: int):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE support_tickets
                SET review_status = 'rejected',
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND review_status = 'pending'
                  AND generated_answer IS NOT NULL
                RETURNING id, review_status, reviewed_at;
                """,
                (ticket_id,),
            )
            return cursor.fetchone()
def get_user_by_email(email: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, password_hash, role,
                       customer_id, is_active
                FROM users
                WHERE email = %s;
                """,
                (email.lower().strip(),),
            )
            return cursor.fetchone()


def get_user_by_id(user_id: int):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, role, customer_id, is_active
                FROM users
                WHERE id = %s;
                """,
                (user_id,),
            )
            return cursor.fetchone()


def create_user(
    email: str,
    password_hash: str,
    customer_id: int,
):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, role, customer_id)
                VALUES (%s, %s, 'customer', %s)
                RETURNING id, email, role, customer_id, is_active;
                """,
                (email.lower().strip(), password_hash, customer_id),
            )
            return cursor.fetchone()

def get_tickets_by_customer(customer_id: int):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM support_tickets
                WHERE customer_id = %s
                ORDER BY id;
                """,
                (customer_id,),
            )
            return cursor.fetchall()

def get_ticket_by_id(ticket_id: int):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM support_tickets
                WHERE id = %s;
                """,
                (ticket_id,),
            )
            return cursor.fetchone()