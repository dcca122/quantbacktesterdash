"""Create strategies table"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date_created", sa.DateTime, nullable=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("parameters", sa.JSON, nullable=False),
        sa.Column("total_return", sa.Float, nullable=False),
        sa.Column("sharpe_ratio", sa.Float, nullable=True),
        sa.Column("max_drawdown", sa.Float, nullable=False),
        sa.Column("tickers", sa.JSON, nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("strategies")
