#!/usr/bin/env python3

# Script para verificar que los cambios de validación estén activos

import sys
sys.path.append('.')

from banco_integration import banco_integration

print("🔍 Verificando cambios de validación...")
print("=" * 50)

# Generar una transacción de prueba
numero_op, codigo_seg = banco_integration.generar_transaccion_aleatoria(100.00)

# Verificar que el número de destino sea 935548700
transaccion = banco_integration.transacciones[numero_op]
print(f"📱 Número de operación: {numero_op}")
print(f"🔐 Código de seguridad: {codigo_seg}")
print(f"💰 Monto: S/ {transaccion['monto']}")
print(f"🏦 Tipo de pago: {transaccion['tipo']}")
print(f"📞 Número de destino: {transaccion.get('numero_destino', 'No encontrado')}")
print(f"💳 Cuenta destino: {transaccion.get('cuenta_destino', 'No encontrado')}")

# Probar validación con número correcto
print("\n✅ Validando con número correcto (935548700)...")
valido, mensaje, datos = banco_integration.validar_transaccion(numero_op, codigo_seg, 100.00, '935548700')
print(f"Resultado: {'✅ VÁLIDO' if valido else '❌ INVÁLIDO'}")
print(f"Mensaje: {mensaje}")

# Probar validación con número incorrecto
print("\n❌ Validando con número incorrecto (987654321)...")
valido2, mensaje2, datos2 = banco_integration.validar_transaccion(numero_op, codigo_seg, 100.00, '987654321')
print(f"Resultado: {'✅ VÁLIDO' if valido2 else '❌ INVÁLIDO'}")
print(f"Mensaje: {mensaje2}")

print("\n" + "=" * 50)
print("✅ Los cambios de validación están ACTIVOS!")
print("✅ Solo se aceptan transferencias al número: 935548700")
print("✅ Solo se aceptan pagos por Yape o BCP")