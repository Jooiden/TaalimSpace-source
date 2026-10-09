from alembic import op
import sqlalchemy as sa
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("time_zone", sa.String(100), nullable=True))

def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_column("time_zone")
        batch.drop_column("birth_date")
