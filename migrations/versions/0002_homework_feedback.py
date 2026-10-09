"""Teacher feedback, separate from AI feedback."""
from alembic import op
import sqlalchemy as sa
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("homework_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("homework_id", sa.Integer(), sa.ForeignKey("homework.id"), unique=True, nullable=False),
        sa.Column("teacher_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("lesson_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_lesson_messages_lesson_id", "lesson_messages", ["lesson_id"])
def downgrade():
    op.drop_table("lesson_messages")
    op.drop_table("homework_feedback")
