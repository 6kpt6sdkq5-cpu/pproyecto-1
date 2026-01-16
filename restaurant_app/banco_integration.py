import random
import string
from datetime import datetime, timedelta

class BancoIntegration:
    """Clase para simular integración con entidades bancarias"""
    
    def __init__(self):
        # Simular base de datos de transacciones bancarias
        self.transacciones = {}
        self.codigos_seguridad = {}
    
    def generar_transaccion_aleatoria(self, monto, numero_destino=None):
        """Genera una transacción bancaria aleatoria para pruebas - números válidos: 935548700 y 19305019234032"""
        numero_operacion = ''.join(random.choices(string.digits, k=10))
        codigo_seguridad = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Fecha y hora aleatoria dentro de las últimas 24 horas
        fecha_transaccion = datetime.now() - timedelta(hours=random.randint(0, 24))
        
        # Solo permitir Yape o BCP, con destino a números válidos
        tipo_pago = random.choice(['yape', 'bcp'])
        
        # Números de destino válidos
        numeros_validos = ['935548700', '19305019234032']
        numero_destino_final = numero_destino if numero_destino in numeros_validos else random.choice(numeros_validos)
        
        self.transacciones[numero_operacion] = {
            'monto': monto,
            'fecha': fecha_transaccion,
            'estado': 'completada',
            'tipo': tipo_pago,
            'banco_origen': 'BCP' if tipo_pago == 'bcp' else random.choice(['BCP', 'Interbank', 'BBVA', 'Scotiabank']),
            'cuenta_destino': numero_destino_final,  # Número de cuenta/telefono destino
            'numero_destino': numero_destino_final  # Número de destino para validación
        }
        
        self.codigos_seguridad[codigo_seguridad] = {
            'numero_operacion': numero_operacion,
            'fecha_generacion': fecha_transaccion,
            'valido_hasta': fecha_transaccion + timedelta(hours=2),
            'numero_destino': numero_destino_final  # Número de destino para validación
        }
        
        return numero_operacion, codigo_seguridad
    
    def validar_transaccion(self, numero_operacion, codigo_seguridad, monto_esperado, numero_destino_esperado=None):
        """
        Valida una transacción bancaria real
        Retorna: (valido, mensaje, datos_transaccion)
        """
        # Números de destino válidos por defecto
        numeros_validos = ['935548700', '19305019234032']
        
        # Si se especifica un número de destino, usar solo ese
        if numero_destino_esperado:
            numeros_validos = [numero_destino_esperado]
        
        # Verificar si existe el número de operación
        if numero_operacion not in self.transacciones:
            return False, "Número de operación no encontrado", None
        
        # Verificar si existe el código de seguridad
        if codigo_seguridad not in self.codigos_seguridad:
            return False, "Código de seguridad inválido", None
        
        # Verificar que el código pertenezca a la operación
        if self.codigos_seguridad[codigo_seguridad]['numero_operacion'] != numero_operacion:
            return False, "El código de seguridad no corresponde a esta operación", None
        
        # Verificar que el código no haya expirado
        fecha_actual = datetime.now()
        if fecha_actual > self.codigos_seguridad[codigo_seguridad]['valido_hasta']:
            return False, "Código de seguridad expirado", None
        
        # Obtener datos de la transacción
        transaccion = self.transacciones[numero_operacion]
        
        # Verificar número de destino (aceptar 935548700 o 19305019234032)
        numero_destino_actual = transaccion.get('numero_destino', transaccion.get('cuenta_destino', ''))
        if numero_destino_actual not in numeros_validos:
            return False, f"El número de destino no es válido. Solo se aceptan transferencias a: {', '.join(numeros_validos)}", transaccion
        
        # Verificar que sea Yape o BCP
        if transaccion['tipo'] not in ['yape', 'bcp']:
            return False, f"Solo se aceptan transferencias por Yape o cuenta BCP. Tipo encontrado: {transaccion['tipo']}", transaccion
        
        # Verificar monto
        if transaccion['monto'] != monto_esperado:
            return False, f"El monto no coincide. Esperado: S/ {monto_esperado}, Encontrado: S/ {transaccion['monto']}", transaccion
        
        # Verificar que la transacción esté completada
        if transaccion['estado'] != 'completada':
            return False, f"La transacción está en estado: {transaccion['estado']}", transaccion
        
        # Verificar que la transacción sea reciente (últimas 48 horas)
        if fecha_actual - transaccion['fecha'] > timedelta(hours=48):
            return False, "La transacción es demasiado antigua", transaccion
        
        # Éxito - retornar datos completos
        return True, "Transacción validada exitosamente", transaccion
    
    def obtener_reporte_diario(self, fecha):
        """Obtiene reporte de transacciones del día"""
        transacciones_dia = []
        total_dia = 0
        
        for num_op, transaccion in self.transacciones.items():
            if transaccion['fecha'].date() == fecha.date():
                transacciones_dia.append({
                    'numero_operacion': num_op,
                    'monto': transaccion['monto'],
                    'hora': transaccion['fecha'].strftime('%H:%M'),
                    'banco': transaccion['banco_origen'],
                    'estado': transaccion['estado']
                })
                total_dia += transaccion['monto']
        
        return {
            'total_transacciones': len(transacciones_dia),
            'monto_total': total_dia,
            'transacciones': transacciones_dia
        }
    
    def generar_codigos_para_prueba(self, cantidad=5):
        """Genera códigos de prueba para demostración - incluye ambos números de cuenta"""
        codigos = []
        numeros_destino = ['935548700', '19305019234032']
        
        for i in range(cantidad):
            monto = round(random.uniform(10, 500), 2)
            # Alternar entre los dos números de destino
            numero_destino = numeros_destino[i % len(numeros_destino)]
            num_op, cod_seg = self.generar_transaccion_aleatoria(monto, numero_destino)
            codigos.append({
                'numero_operacion': num_op,
                'codigo_seguridad': cod_seg,
                'monto': monto,
                'numero_destino': numero_destino
            })
        return codigos

# Instancia global del banco
banco_integration = BancoIntegration()

# Generar algunas transacciones de prueba al iniciar
print("🔄 Generando transacciones de prueba para el sistema...")
transacciones_prueba = banco_integration.generar_codigos_para_prueba(10)
for transaccion in transacciones_prueba:
    print(f"✅ Transacción generada - Op: {transaccion['numero_operacion']}, Código: {transaccion['codigo_seguridad']}, Monto: S/ {transaccion['monto']}")