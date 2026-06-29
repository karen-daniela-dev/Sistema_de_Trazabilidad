"""Add performance indexes for applications, interviews, alerts and profiles.

Revision ID: 20260626_add_performance_indexes
Revises: 
Create Date: 2026-06-26 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '20260626_add_performance_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        'ix_aplicaciones_usuario_estado',
        'aplicaciones',
        ['usuario_id', 'estado'],
        unique=False,
    )
    op.create_index(
        'ix_aplicaciones_fecha_usuario',
        'aplicaciones',
        ['fecha_aplicacion', 'usuario_id'],
        unique=False,
    )
    op.create_index(
        'ix_entrevistas_aplicacion_fecha',
        'entrevistas',
        ['aplicacion_id', 'fecha'],
        unique=False,
    )
    op.create_index(
        'ix_alertas_target_leida_created',
        'alertas',
        ['target_id', 'target_type', 'leida', 'created_at'],
        unique=False,
    )
    op.create_index(
        'ix_aprendiz_perfil_tutor_cohorte',
        'aprendiz_perfil',
        ['tutor_id', 'cohorte_id'],
        unique=False,
    )
    op.create_index(
        'ix_usuarios_rol_activo',
        'usuarios',
        ['rol', 'activo'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_usuarios_rol_activo', table_name='usuarios')
    op.drop_index('ix_aprendiz_perfil_tutor_cohorte', table_name='aprendiz_perfil')
    op.drop_index('ix_alertas_target_leida_created', table_name='alertas')
    op.drop_index('ix_entrevistas_aplicacion_fecha', table_name='entrevistas')
    op.drop_index('ix_aplicaciones_fecha_usuario', table_name='aplicaciones')
    op.drop_index('ix_aplicaciones_usuario_estado', table_name='aplicaciones')
