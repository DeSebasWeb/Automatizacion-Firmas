"""Validador de longitudes de cédulas para ensemble OCR."""
from typing import Optional
from ....domain.entities import CedulaRecord


class LengthValidator:
    """
    Valida y maneja diferencias de longitud entre cédulas de diferentes OCR.

    Responsabilidad única: Determinar qué cédula usar cuando las longitudes difieren,
    basándose en patrones estándar de cédulas colombianas.

    Orden de prioridad de longitudes:
    1. 10 dígitos - Cédulas colombianas modernas (más común)
    2. 8 dígitos - Cédulas colombianas antiguas (segunda más común)
    3. 9 dígitos - Menos común
    4. Otros - Muy raro, probablemente error
    """

    # Prioridad por longitud (mayor número = mayor prioridad)
    LENGTH_PRIORITIES = {
        10: 3,  # Máxima prioridad (cédulas modernas)
        8: 2,   # Segunda prioridad (cédulas antiguas)
        9: 1,   # Tercera prioridad (menos común)
    }

    @staticmethod
    def validate_and_choose(
        primary: CedulaRecord,
        secondary: CedulaRecord,
        verbose: bool = False
    ) -> Optional[CedulaRecord]:
        """
        Valida longitudes y elige la mejor cédula cuando difieren.

        ESTRATEGIA:
        1. Si longitudes son iguales → return None (permite comparación dígito por dígito)
        2. Si difieren → elegir por prioridad de longitud
        3. Si misma prioridad → elegir por confianza

        Args:
            primary: Registro del OCR primario
            secondary: Registro del OCR secundario
            verbose: Si imprimir logging detallado

        Returns:
            CedulaRecord elegido si las longitudes difieren, None si son iguales
        """
        primary_text = primary.cedula.value
        secondary_text = secondary.cedula.value
        primary_len = len(primary_text)
        secondary_len = len(secondary_text)

        # Si longitudes son iguales, no hay nada que validar
        if primary_len == secondary_len:
            return None

        # Longitudes difieren - mostrar advertencia
        if verbose:
            print(f"\n{'='*80}")
            print("⚠️ LONGITUDES DIFERENTES - Eligiendo por longitud estándar")
            print(f"{'='*80}")
            print(f"Primary:   {primary_text} ({primary_len} dígitos, "
                  f"conf: {primary.confidence.as_percentage():.1f}%)")
            print(f"Secondary: {secondary_text} ({secondary_len} dígitos, "
                  f"conf: {secondary.confidence.as_percentage():.1f}%)")
            print(f"{'='*80}\n")

        # Obtener prioridades
        primary_priority = LengthValidator.LENGTH_PRIORITIES.get(primary_len, 0)
        secondary_priority = LengthValidator.LENGTH_PRIORITIES.get(secondary_len, 0)

        # Comparar por prioridad de longitud
        if primary_priority > secondary_priority:
            if verbose:
                print(f"✅ ELEGIDO Primary: {primary_text}")
                print(f"   Razón: {primary_len} dígitos es más común que {secondary_len} dígitos")
                print(f"   Confianza: {primary.confidence.as_percentage():.1f}%\n")
            return primary

        elif secondary_priority > primary_priority:
            if verbose:
                print(f"✅ ELEGIDO Secondary: {secondary_text}")
                print(f"   Razón: {secondary_len} dígitos es más común que {primary_len} dígitos")
                print(f"   Confianza: {secondary.confidence.as_percentage():.1f}%\n")
            return secondary

        else:
            # Misma prioridad de longitud → elegir por confianza
            if primary.confidence.value >= secondary.confidence.value:
                if verbose:
                    print(f"✅ ELEGIDO Primary: {primary_text}")
                    print(f"   Razón: Misma prioridad de longitud ({primary_len} dígitos), "
                          f"mayor confianza")
                    print(f"   Confianza: {primary.confidence.as_percentage():.1f}% vs "
                          f"{secondary.confidence.as_percentage():.1f}%\n")
                return primary
            else:
                if verbose:
                    print(f"✅ ELEGIDO Secondary: {secondary_text}")
                    print(f"   Razón: Misma prioridad de longitud ({secondary_len} dígitos), "
                          f"mayor confianza")
                    print(f"   Confianza: {secondary.confidence.as_percentage():.1f}% vs "
                          f"{ primary.confidence.as_percentage():.1f}%\n")
                return secondary

    @staticmethod
    def is_standard_length(length: int) -> bool:
        """
        Verifica si una longitud es estándar para cédulas colombianas.

        Args:
            length: Longitud a verificar

        Returns:
            True si es longitud estándar (8, 9, o 10 dígitos)
        """
        return length in LengthValidator.LENGTH_PRIORITIES

    @staticmethod
    def get_priority_description(length: int) -> str:
        """
        Obtiene descripción de prioridad para una longitud.

        Args:
            length: Longitud de la cédula

        Returns:
            Descripción textual de la prioridad
        """
        if length == 10:
            return "Máxima prioridad (cédulas modernas)"
        elif length == 8:
            return "Segunda prioridad (cédulas antiguas)"
        elif length == 9:
            return "Tercera prioridad (menos común)"
        else:
            return "Baja prioridad (longitud no estándar)"
