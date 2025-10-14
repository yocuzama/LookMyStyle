"""init_uuid"""

from typing import Sequence, Union
from alembic import op

revision: str = "9b7d7bc4b238"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _exec(sql: str) -> None:
    op.execute(sql)


def _drop_all_fks_on(table_name: str) -> None:
    _exec(f"""
    DECLARE @sql nvarchar(max) = N'';
    SELECT @sql = @sql + N'ALTER TABLE [' + SCHEMA_NAME(t.schema_id) + N'].[' + t.name +
                  N'] DROP CONSTRAINT [' + fk.name + N'];'
    FROM sys.foreign_keys fk
    JOIN sys.tables t ON t.object_id = fk.parent_object_id
    WHERE t.name = N'{table_name}';
    IF @sql <> N'' EXEC sp_executesql @sql;
    """)


def _drop_all_fks_referencing(table_name: str) -> None:
    _exec(f"""
    DECLARE @sql nvarchar(max) = N'';
    SELECT @sql = @sql + N'ALTER TABLE [' + SCHEMA_NAME(tp.schema_id) + N'].[' + tp.name +
                  N'] DROP CONSTRAINT [' + fk.name + N'];'
    FROM sys.foreign_keys fk
    JOIN sys.tables tp ON tp.object_id = fk.parent_object_id
    JOIN sys.tables tr ON tr.object_id = fk.referenced_object_id
    WHERE tr.name = N'{table_name}';
    IF @sql <> N'' EXEC sp_executesql @sql;
    """)


def _drop_pk(table_name: str) -> None:
    _exec(f"""
    DECLARE @pk sysname, @schema sysname, @sql nvarchar(max);
    SELECT @pk = kc.name, @schema = SCHEMA_NAME(t.schema_id)
    FROM sys.key_constraints kc
    JOIN sys.tables t ON t.object_id = kc.parent_object_id
    WHERE kc.type = 'PK' AND t.name = N'{table_name}';
    IF @pk IS NOT NULL
    BEGIN
        SET @sql = N'ALTER TABLE [' + @schema + N'].[' + N'{table_name}' + N'] DROP CONSTRAINT [' + @pk + N']';
        EXEC sp_executesql @sql;
    END
    """)


def _drop_index_if_exists(table_name: str, index_name: str) -> None:
    _exec(f"""
    IF EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = N'{index_name}' AND object_id = OBJECT_ID(N'dbo.{table_name}')
    )
        DROP INDEX [{index_name}] ON [dbo].[{table_name}];
    """)


def _drop_unique_if_exists(table_name: str, uq_name: str) -> None:
    _exec(f"""
    IF EXISTS (
        SELECT 1
        FROM sys.key_constraints
        WHERE type = 'UQ' AND name = N'{uq_name}' AND parent_object_id = OBJECT_ID(N'dbo.{table_name}')
    )
    BEGIN
        ALTER TABLE [dbo].[{table_name}] DROP CONSTRAINT [{uq_name}];
    END
    """)
    _drop_index_if_exists(table_name, uq_name)


def upgrade() -> None:
    _drop_all_fks_on('carrito_items')
    _drop_all_fks_on('carritos')
    _drop_all_fks_on('clientes')
    _drop_all_fks_on('productos')
    _drop_all_fks_referencing('carrito_items')
    _drop_all_fks_referencing('carritos')
    _drop_all_fks_referencing('clientes')
    _drop_all_fks_referencing('productos')

    _drop_index_if_exists('carrito_items', 'ix_carrito_items_id')
    _drop_index_if_exists('carrito_items', 'ix_carrito_items_carrito_id')
    _drop_index_if_exists('carrito_items', 'ix_carrito_items_producto_id')
    _drop_index_if_exists('carritos', 'ix_carritos_id')
    _drop_index_if_exists('carritos', 'ix_carritos_cliente_id')
    _drop_index_if_exists('clientes', 'ix_clientes_id')
    _drop_index_if_exists('productos', 'ix_productos_id')

    _exec("ALTER TABLE [dbo].[clientes]  ADD [id_uuid] UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID();")
    _exec("ALTER TABLE [dbo].[productos] ADD [id_uuid] UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID();")
    _exec("ALTER TABLE [dbo].[carritos]  ADD [id_uuid] UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(), [cliente_id_uuid] UNIQUEIDENTIFIER NULL;")
    _exec("ALTER TABLE [dbo].[carrito_items] ADD [id_uuid] UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(), [carrito_id_uuid] UNIQUEIDENTIFIER NULL, [producto_id_uuid] UNIQUEIDENTIFIER NULL;")

    _exec("""
    UPDATE c SET c.cliente_id_uuid = cl.id_uuid
    FROM [dbo].[carritos] c
    JOIN [dbo].[clientes] cl ON cl.id = c.cliente_id;
    """)
    _exec("""
    UPDATE ci SET ci.carrito_id_uuid = ca.id_uuid
    FROM [dbo].[carrito_items] ci
    JOIN [dbo].[carritos] ca ON ca.id = ci.carrito_id;
    """)
    _exec("""
    UPDATE ci SET ci.producto_id_uuid = pr.id_uuid
    FROM [dbo].[carrito_items] ci
    JOIN [dbo].[productos] pr ON pr.id = ci.producto_id;
    """)

    _drop_pk('carrito_items')
    _drop_pk('carritos')
    _drop_pk('clientes')
    _drop_pk('productos')

    _drop_unique_if_exists('carrito_items', 'uq_carrito_producto')

    _exec("ALTER TABLE [dbo].[carrito_items] DROP COLUMN [producto_id];")
    _exec("ALTER TABLE [dbo].[carrito_items] DROP COLUMN [carrito_id];")
    _exec("ALTER TABLE [dbo].[carritos] DROP COLUMN [cliente_id];")

    _exec("EXEC sp_rename 'dbo.carrito_items.id',     'id_old',     'COLUMN';")
    _exec("EXEC sp_rename 'dbo.carritos.id',          'id_old',     'COLUMN';")
    _exec("EXEC sp_rename 'dbo.clientes.id',          'id_old',     'COLUMN';")
    _exec("EXEC sp_rename 'dbo.productos.id',         'id_old',     'COLUMN';")

    _exec("EXEC sp_rename 'dbo.carrito_items.id_uuid','id',         'COLUMN';")
    _exec("EXEC sp_rename 'dbo.carritos.id_uuid',     'id',         'COLUMN';")
    _exec("EXEC sp_rename 'dbo.clientes.id_uuid',     'id',         'COLUMN';")
    _exec("EXEC sp_rename 'dbo.productos.id_uuid',    'id',         'COLUMN';")

    _exec("EXEC sp_rename 'dbo.carritos.cliente_id_uuid',  'cliente_id',  'COLUMN';")
    _exec("EXEC sp_rename 'dbo.carrito_items.carrito_id_uuid', 'carrito_id', 'COLUMN';")
    _exec("EXEC sp_rename 'dbo.carrito_items.producto_id_uuid','producto_id','COLUMN';")

    _exec("ALTER TABLE [dbo].[carrito_items] DROP COLUMN [id_old];")
    _exec("ALTER TABLE [dbo].[carritos]      DROP COLUMN [id_old];")
    _exec("ALTER TABLE [dbo].[clientes]      DROP COLUMN [id_old];")
    _exec("ALTER TABLE [dbo].[productos]     DROP COLUMN [id_old];")

    _exec("ALTER TABLE [dbo].[clientes]  ADD CONSTRAINT [PK_clientes]  PRIMARY KEY ([id]);")
    _exec("ALTER TABLE [dbo].[productos] ADD CONSTRAINT [PK_productos] PRIMARY KEY ([id]);")
    _exec("ALTER TABLE [dbo].[carritos]  ADD CONSTRAINT [PK_carritos]  PRIMARY KEY ([id]);")
    _exec("ALTER TABLE [dbo].[carrito_items] ADD CONSTRAINT [PK_carrito_items] PRIMARY KEY ([id]);")

    _exec("""
    ALTER TABLE [dbo].[carritos]
      ADD CONSTRAINT [FK_carritos_clientes_cliente_id]
      FOREIGN KEY ([cliente_id]) REFERENCES [dbo].[clientes]([id]) ON DELETE CASCADE;
    """)
    _exec("""
    ALTER TABLE [dbo].[carrito_items]
      ADD CONSTRAINT [FK_carrito_items_carritos_carrito_id]
      FOREIGN KEY ([carrito_id]) REFERENCES [dbo].[carritos]([id]) ON DELETE CASCADE;
    """)
    _exec("""
    ALTER TABLE [dbo].[carrito_items]
      ADD CONSTRAINT [FK_carrito_items_productos_producto_id]
      FOREIGN KEY ([producto_id]) REFERENCES [dbo].[productos]([id]);
    """)

    _exec("""
    ALTER TABLE [dbo].[clientes]
      ADD [creado_por] UNIQUEIDENTIFIER NULL,
          [actualizado_por] UNIQUEIDENTIFIER NULL,
          [fecha_creacion] DATETIMEOFFSET NOT NULL CONSTRAINT DF_clientes_fecha_creacion DEFAULT SYSUTCDATETIME(),
          [fecha_actualizacion] DATETIMEOFFSET NULL CONSTRAINT DF_clientes_fecha_actualizacion DEFAULT SYSUTCDATETIME();
    """)
    _exec("""
    ALTER TABLE [dbo].[productos]
      ADD [creado_por] UNIQUEIDENTIFIER NULL,
          [actualizado_por] UNIQUEIDENTIFIER NULL,
          [fecha_creacion] DATETIMEOFFSET NOT NULL CONSTRAINT DF_productos_fecha_creacion DEFAULT SYSUTCDATETIME(),
          [fecha_actualizacion] DATETIMEOFFSET NULL CONSTRAINT DF_productos_fecha_actualizacion DEFAULT SYSUTCDATETIME();
    """)
    _exec("""
    ALTER TABLE [dbo].[carritos]
      ADD [creado_por] UNIQUEIDENTIFIER NULL,
          [actualizado_por] UNIQUEIDENTIFIER NULL,
          [fecha_creacion] DATETIMEOFFSET NOT NULL CONSTRAINT DF_carritos_fecha_creacion DEFAULT SYSUTCDATETIME(),
          [fecha_actualizacion] DATETIMEOFFSET NULL CONSTRAINT DF_carritos_fecha_actualizacion DEFAULT SYSUTCDATETIME();
    """)
    _exec("""
    ALTER TABLE [dbo].[carrito_items]
      ADD [creado_por] UNIQUEIDENTIFIER NULL,
          [actualizado_por] UNIQUEIDENTIFIER NULL,
          [fecha_creacion] DATETIMEOFFSET NOT NULL CONSTRAINT DF_carrito_items_fecha_creacion DEFAULT SYSUTCDATETIME(),
          [fecha_actualizacion] DATETIMEOFFSET NULL CONSTRAINT DF_carrito_items_fecha_actualizacion DEFAULT SYSUTCDATETIME();
    """)

    _exec("""
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'ix_clientes_email'
      AND object_id = OBJECT_ID(N'[dbo].[clientes]')
)
    CREATE UNIQUE INDEX [ix_clientes_email] ON [dbo].[clientes]([email]);
""")

    _exec("""
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'ix_productos_nombre'
      AND object_id = OBJECT_ID(N'[dbo].[productos]')
)
    CREATE INDEX [ix_productos_nombre] ON [dbo].[productos]([nombre]);
""")

    _exec("""
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'ix_productos_categoria'
      AND object_id = OBJECT_ID(N'[dbo].[productos]')
)
    CREATE INDEX [ix_productos_categoria] ON [dbo].[productos]([categoria]);
""")

def downgrade() -> None:
    raise NotImplementedError("No reversible")
