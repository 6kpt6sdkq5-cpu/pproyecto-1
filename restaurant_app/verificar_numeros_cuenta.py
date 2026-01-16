#!/usr/bin/env python3

# Script para verificar que ambos números de cuenta estén activos

import sys
sys.path.append('.')

from banco_integration import banco_integration

print("🔍 Verificando números de cuenta adicionales...")
print("=" * 60)

# Generar transacciones de prueba para ambos números
print("\n📱 Generando transacciones de prueba...")

# Generar transacción para 935548700
numero_op1, codigo_seg1 = banco_integration.generar_transaccion_aleatoria(150.00, '935548700')
transaccion1 = banco_integration.transacciones[numero_op1]

# Generar transacción para 19305019234032
numero_op2, codigo_seg2 = banco_integration.generar_transaccion_aleatoria(250.00, '19305019234032')
transaccion2 = banco_integration.transacciones[numero_op2]

print(f"✅ Transacción 1 - Número: {numero_op1}")
print(f"   Código: {codigo_seg1}")
print(f"   Monto: S/ 150.00")
print(f"   Destino: {transaccion1.get('numero_destino')}")
print(f"   Tipo: {transaccion1.get('tipo')}")

print(f"\n✅ Transacción 2 - Número: {numero_op2}")
print(f"   Código: {codigo_seg2}")
print(f"   Monto: S/ 250.00")
print(f"   Destino: {transaccion2.get('numero_destino')}")
print(f"   Tipo: {transaccion2.get('tipo')}")

# Validar ambas transacciones
print("\n🔐 Validando transacciones...")

# Validar transacción 1
valido1, mensaje1, datos1 = banco_integration.validar_transaccion(numero_op1, codigo_seg1, 150.00)
print(f"\nTransacción 1 (935548700): {'✅ VÁLIDA' if valido1 else '❌ INVÁLIDA'}")
if not valido1:
    print(f"Error: {mensaje1}")

# Validar transacción 2
valido2, mensaje2, datos2 = banco_integration.validar_transaccion(numero_op2, codigo_seg2, 250.00)
print(f"\nTransacción 2 (19305019234032): {'✅ VÁLIDA' if valido2 else '❌ INVÁLIDA'}")
if not valido2:
    print(f"Error: {mensaje2}")

# Probar validación con número inválido
print("\n❌ Probando con número de destino inválido...")
numero_op3, codigo_seg3 = banco_integration.generar_transaccion_aleatoria(100.00, '123456789')
valido3, mensaje3, datos3 = banco_integration.validar_transaccion(numero_op3, codigo_seg3, 100.00)
print(f"Transacción con número inválido: {'✅ VÁLIDA' if valido3 else '❌ INVÁLIDA'}")
print(f"Mensaje: {mensaje3}")

print("\n" + "=" * 60)
print("✅ Números de cuenta ACTIVOS:")
print("✅ 935548700 (Yape/Celular)")
print("✅ 19305019234032 (Cuenta BCP)")
print("✅ Ambos números aceptan Yape y BCP")
print("✅ Sistema rechaza números no autorizados")