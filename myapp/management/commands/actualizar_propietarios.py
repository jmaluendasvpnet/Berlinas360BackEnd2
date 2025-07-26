import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from myapp.models import Propietario  # ajuste el import según su proyecto


class Command(BaseCommand):
    help = "Actualiza dirección, ciudad y departamento de Propietario usando validator1.xlsx y validator2.xlsx"

    def add_arguments(self, parser):
        parser.add_argument("validator1", type=str, help="Ruta a validator1.xlsx")
        parser.add_argument("validator2", type=str, help="Ruta a validator2.xlsx")

    def handle(self, *args, **options):
        file1 = Path(options["validator1"])
        file2 = Path(options["validator2"])

        if not file1.exists() or not file2.exists():
            raise CommandError("Alguno de los archivos no existe.")

        updates = []
        updates += self._collect_updates_validator1(file1)
        updates += self._collect_updates_validator2(file2)

        if not updates:
            print("No se encontraron propietarios para actualizar.")
            return

        print("\nPREVISUALIZACIÓN DE CAMBIOS\n")
        print(f'{"ID":<6} {"Identificación":<20} {"Campo":<12} {"Valor actual":<40} {"Nuevo valor":<40}')
        print("-" * 120)
        for item in updates:
            prop = item["obj"]
            for campo, vals in item["changes"].items():
                print(
                    f'{prop.id:<6} {prop.identificacion:<20} {campo:<12} '
                    f'{(vals["old"] or ""):<40} {(vals["new"] or ""):<40}'
                )

        if input("\n¿Confirmar actualización? (y/n): ").strip().lower() != "y":
            print("Operación cancelada.")
            return

        with transaction.atomic():
            for item in updates:
                prop = item["obj"]
                for campo, vals in item["changes"].items():
                    setattr(prop, campo, vals["new"])
                prop.save(update_fields=list(item["changes"].keys()))

        print("Actualización completada.")

    # ------------------------------------------------------------------ #
    #                                XLSX 1                              #
    # ------------------------------------------------------------------ #
    def _collect_updates_validator1(self, path: Path):
        df = pd.read_excel(path)
        mappings = [
            {
                "id": "Identificacion Prop 1",
                "direccion": "Direccion",
                "ciudad": "CIUDAD 1 prp",
                "departamento": "DEPARTAMENTO Prop 1",
            },
            {
                "id": "Identificacion Prop 2",
                "direccion": "Direccion 2",
                "ciudad": "CIUDAD 2",
                "departamento": "DEPARTAMENTO 2",
            },
        ]
        return self._extract_updates(df, mappings)

    # ------------------------------------------------------------------ #
    #                                XLSX 2                              #
    # ------------------------------------------------------------------ #
    def _collect_updates_validator2(self, path: Path):
        df = pd.read_excel(path)
        cols = df.columns.tolist()

        def cname(base: str, idx: int):
            return base if idx == 0 else f"{base}.{idx}"

        mappings = []
        for idx in range(2):
            id_col = cname("CEDULA", idx)
            dir_col = cname("DIRECCION", idx)
            city_col = cname("CIUDAD RESIDENCIA", idx)
            if id_col in cols:
                mappings.append(
                    {
                        "id": id_col,
                        "direccion": dir_col if dir_col in cols else None,
                        "ciudad": city_col if city_col in cols else None,
                        "departamento": None,
                    }
                )
        return self._extract_updates(df, mappings)

    # ------------------------------------------------------------------ #
    #                         EXTRACCIÓN GENÉRICA                        #
    # ------------------------------------------------------------------ #
    def _extract_updates(self, df, mappings):
        updates = []
        for _, row in df.iterrows():
            for mp in mappings:
                ident = self._clean(row.get(mp["id"]))
                if not ident:
                    continue

                try:
                    prop = Propietario.objects.get(identificacion=ident)
                except Propietario.DoesNotExist:
                    continue

                change_set = {}
                if mp.get("direccion"):
                    self._maybe_add_change(prop, "direccion", self._clean(row.get(mp["direccion"])), change_set)
                if mp.get("ciudad"):
                    self._maybe_add_change(prop, "ciudad", self._clean(row.get(mp["ciudad"])), change_set)
                if mp.get("departamento"):
                    self._maybe_add_change(prop, "departamento", self._clean(row.get(mp["departamento"])), change_set)

                if change_set:
                    updates.append({"obj": prop, "changes": change_set})

        return updates

    # ------------------------------------------------------------------ #
    #                               UTILS                                #
    # ------------------------------------------------------------------ #
    def _maybe_add_change(self, prop, field: str, new_val, change_set: dict):
        if new_val and new_val != getattr(prop, field):
            change_set[field] = {"old": getattr(prop, field), "new": new_val}

    @staticmethod
    def _clean(value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        return str(value).strip()
