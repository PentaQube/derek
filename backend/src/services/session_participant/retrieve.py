from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from src.core.exceptions import NotFoundError
from src.models.user import User
from src.models.question import Question
from src.models.session import (
    SessionParticipant,
    SessionParticipantQuestion,
    SessionQuestion,
    Session as SessionModel,
)
from .common.statements import base_select_stmt


def retrieve_session_participant_service(
    *, session: Session, participant_id: int, current_user: User
) -> SessionParticipant:
    # Auth check

    stmt = base_select_stmt.where(SessionParticipant.id == participant_id)
    participant = session.scalar(stmt)

    if not participant:
        raise NotFoundError(
            f"Session participant with ID {participant_id} not found."
        )

    return participant


def get_participiant_last_question(
    *, session: Session, session_id: int, participant_id: int
):

    participant = session.get(SessionParticipant, participant_id)

    if not participant or int(participant.session_id) != int(session_id):
        raise NotFoundError(
            f"Session participant not found: ID {participant_id}, session ID {session_id}."
        )

    last_triggered_question_id = session.scalar(
        select(SessionModel.last_triggered_question_id).where(
            SessionModel.id == session_id
        )
    )

    last_participant_question_id = session.scalar(
        select(SessionQuestion.question_id)
        .join(
            SessionParticipantQuestion,
            SessionQuestion.id == SessionParticipantQuestion.session_question_id,
        )
        .where(
            SessionParticipantQuestion.session_participant_id == participant_id,
            SessionQuestion.session_id == session_id,
        )
        .order_by(SessionQuestion.position.desc())
        .limit(1)
    )

    if last_participant_question_id == last_triggered_question_id:
        source = "participant"
    else:
        source = "session"

    session_question = session.scalar(
        select(SessionQuestion)
        .join(Question, Question.id == SessionQuestion.question_id)
        .options(joinedload(SessionQuestion.question))
        .where(
            SessionQuestion.session_id == session_id,
            SessionQuestion.question_id == last_triggered_question_id,
        )
    )

    #!  total_questions_attended
    # SELECT COUNT(spq.id) AS total_questions_attended FROM session_participant_question spq
    # JOIN session_question sq ON sq.id = spq.session_question_id
    # WHERE spq.session_participant_id = 210
    # AND sq.session_id = 66;

    total_questions_attended = session.scalar(
        select(func.count(SessionParticipantQuestion.id))
        .join(
            SessionQuestion,
            SessionQuestion.id == SessionParticipantQuestion.session_question_id,
        )
        .where(
            SessionParticipantQuestion.session_participant_id == participant_id,
            SessionQuestion.session_id == session_id,
        )
    )

    #! Get last Question
    # SELECT spq.*, q.*
    # FROM session_participant_question spq
    # JOIN session_question sq ON sq.id = spq.session_question_id
    # JOIN question q ON q.id = sq.question_id
    #     WHERE
    # spq.session_participant_id = 210
    #     AND
    # sq.session_id = 66
    # ORDER BY
    #     sq.position DESC
    # LIMIT 1;

    # Initialize response variables
    last_question = None
    last_answer_status = None
    last_answer = None

    if source == "participant":
        last_spq = session.scalar(
            select(SessionParticipantQuestion)
            .join(
                SessionQuestion,
                SessionQuestion.id == SessionParticipantQuestion.session_question_id,
            )
            .join(Question, Question.id == SessionQuestion.question_id)
            .options(
                joinedload(SessionParticipantQuestion.session_question).joinedload(
                    SessionQuestion.question
                ),
                joinedload(SessionParticipantQuestion.answer_status),
                joinedload(SessionParticipantQuestion.selected_options),
            )
            .where(
                SessionParticipantQuestion.session_participant_id == participant_id,
                SessionQuestion.session_id == session_id,
            )
            .order_by(SessionQuestion.position.desc())
            .limit(1)
        )

        if last_spq is not None:
            question = last_spq.session_question.question
            last_question = {
                "id": question.id,
                "text": question.title,
                "type": question.answer_type.code if question.answer_type else None,
                "options": [
                    {"id": opt.id, "text": opt.option_text}
                    for opt in (question.options or [])
                ],
            }

            status = last_spq.answer_status
            last_answer_status = status.code if status else None

            option_ids = [
                opt.option_id
                for opt in (last_spq.selected_options or [])
                if opt.option_id is not None
            ]

            last_answer = {
                "option_id": option_ids[0] if len(option_ids) == 1 else None,
                "option_ids": option_ids if len(option_ids) > 1 else None,
                "answer_text": last_spq.answer_text,
            }

    elif source == "session" and session_question:
        question = session.scalar(
            select(Question)
            .options(joinedload(Question.options))
            .where(Question.id == last_triggered_question_id)
        )

        if question:
            last_question = {
                "id": question.id,
                "text": question.title,
                "type": question.answer_type.code if question.answer_type else None,
                "time_limit_ms": question.time_limit_ms,
                "options": [
                    {"id": opt.id, "text": opt.option_text}
                    for opt in (question.options or [])
                ],
            }

    return {
        "total_questions_attended": int(total_questions_attended or 0),
        "last_question": last_question,
        "last_answer_status": last_answer_status,
        "last_answer": last_answer,
    }
