"""initial schema

Revision ID: 8fd75e8a0d7b
Revises:
Create Date: 2026-02-17 23:37:15.413498

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET, TSRANGE


# revision identifiers, used by Alembic.
revision = '8fd75e8a0d7b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. users (no FK deps)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('role', sa.Enum('admin', 'profesional', name='user_role_enum'), nullable=False, server_default='profesional'),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # 2. pacientes (no FK deps)
    op.create_table('pacientes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('apellido', sa.String(length=100), nullable=False),
        sa.Column('dni', sa.String(length=15), nullable=False),
        sa.Column('telefono', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('obra_social', sa.String(length=100), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dni'),
    )

    # 3. consultorios (no FK deps)
    op.create_table('consultorios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=50), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )

    # 4. profesionales (FK -> users)
    op.create_table('profesionales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('apellido', sa.String(length=100), nullable=False),
        sa.Column('especialidad', sa.String(length=100), nullable=True),
        sa.Column('telefono', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    # 5. profesional_consultorio (FK -> profesionales, consultorios)
    op.create_table('profesional_consultorio',
        sa.Column('profesional_id', sa.Integer(), nullable=False),
        sa.Column('consultorio_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['profesional_id'], ['profesionales.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['consultorio_id'], ['consultorios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('profesional_id', 'consultorio_id'),
    )

    # 6. turnos (FK -> pacientes, profesionales, consultorios, users)
    op.create_table('turnos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('profesional_id', sa.Integer(), nullable=False),
        sa.Column('consultorio_id', sa.Integer(), nullable=False),
        sa.Column('durante', TSRANGE(), nullable=False),
        sa.Column('estado', sa.Enum('reservado', 'confirmado', 'atendido', 'cancelado', name='turno_estado_enum'), nullable=False, server_default='reservado'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('cancelado_por', sa.Integer(), nullable=True),
        sa.Column('cancelado_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('motivo_cancelacion', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id']),
        sa.ForeignKeyConstraint(['profesional_id'], ['profesionales.id']),
        sa.ForeignKeyConstraint(['consultorio_id'], ['consultorios.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['cancelado_por'], ['users.id']),
        sa.CheckConstraint(
            "upper(durante) - lower(durante) >= interval '15 minutes'"
            " AND upper(durante) - lower(durante) <= interval '120 minutes'",
            name='duracion_valida',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    # Exclusion constraints (require btree_gist)
    op.execute("""
        ALTER TABLE turnos ADD CONSTRAINT no_solapamiento_consultorio
        EXCLUDE USING gist (consultorio_id WITH =, durante WITH &&)
        WHERE (estado != 'cancelado')
    """)
    op.execute("""
        ALTER TABLE turnos ADD CONSTRAINT no_solapamiento_profesional
        EXCLUDE USING gist (profesional_id WITH =, durante WITH &&)
        WHERE (estado != 'cancelado')
    """)
    op.execute("""
        ALTER TABLE turnos ADD CONSTRAINT no_solapamiento_paciente
        EXCLUDE USING gist (paciente_id WITH =, durante WITH &&)
        WHERE (estado != 'cancelado')
    """)
    op.create_index('ix_turnos_durante_gist', 'turnos', ['durante'], postgresql_using='gist')
    op.execute("CREATE INDEX ix_turnos_consultorio_fecha ON turnos (consultorio_id, (lower(durante)::date))")
    op.execute("CREATE INDEX ix_turnos_profesional_fecha ON turnos (profesional_id, (lower(durante)::date))")

    # 7. turnos_audit (FK -> turnos, users)
    op.create_table('turnos_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('turno_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('accion', sa.String(length=50), nullable=False),
        sa.Column('campo_modificado', sa.String(length=50), nullable=True),
        sa.Column('valor_anterior', sa.Text(), nullable=True),
        sa.Column('valor_nuevo', sa.Text(), nullable=True),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['turno_id'], ['turnos.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_turnos_audit_turno_id', 'turnos_audit', ['turno_id'])
    op.create_index('ix_turnos_audit_user_id', 'turnos_audit', ['user_id'])

    # 8. turnos_series_log (FK -> pacientes, profesionales, users)
    op.create_table('turnos_series_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('serie_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('profesional_id', sa.Integer(), nullable=False),
        sa.Column('fecha_inicio', sa.Date(), nullable=False),
        sa.Column('fecha_limite', sa.Date(), nullable=False),
        sa.Column('cada_n_semanas', sa.Integer(), nullable=False),
        sa.Column('patrones_json', sa.JSON(), nullable=False),
        sa.Column('total_intentados', sa.Integer(), nullable=False),
        sa.Column('total_creados', sa.Integer(), nullable=False),
        sa.Column('total_fallidos', sa.Integer(), nullable=False),
        sa.Column('fallidos_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id']),
        sa.ForeignKeyConstraint(['profesional_id'], ['profesionales.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_turnos_series_log_serie_id', 'turnos_series_log', ['serie_id'])
    op.create_index('ix_turnos_series_log_user_id', 'turnos_series_log', ['user_id'])


def downgrade():
    op.drop_table('turnos_series_log')
    op.drop_table('turnos_audit')
    op.drop_index('ix_turnos_profesional_fecha', 'turnos')
    op.drop_index('ix_turnos_consultorio_fecha', 'turnos')
    op.drop_index('ix_turnos_durante_gist', 'turnos')
    op.drop_table('turnos')
    op.drop_table('profesional_consultorio')
    op.drop_table('profesionales')
    op.drop_table('consultorios')
    op.drop_table('pacientes')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS turno_estado_enum")
    op.execute("DROP TYPE IF EXISTS user_role_enum")
