import aio_pika
import json
class RabbitMQService:
    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self, rabbitmq_url: str):
        """Conectar a RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Declarar el exchange topic (opcional - si quieres asegurar que existe)
            self.exchange = await self.channel.declare_exchange(
                "amq.topic", 
                aio_pika.ExchangeType.TOPIC,
                durable=True,
                passive=True  # Solo verifica que existe, no lo crea
            )
            
            print("Conexión a RabbitMQ establecida exitosamente")
        except Exception as e:
            print(f"Error conectando a RabbitMQ: {e}")
            raise

    async def close(self):
        """Cerrar conexión RabbitMQ"""
        if self.connection:
            await self.connection.close()

    async def send_cam_data(self, cam_data: dict):
        """Enviar datos CAM a RabbitMQ"""
        try:
            if not self.channel:
                raise Exception("Canal de RabbitMQ no disponible")

            # Crear mensaje
            message_body = json.dumps(cam_data).encode()
            
            # Publicar en el exchange
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="cam"
            )
            print(f"Datos CAM enviados a RabbitMQ - Prototype: {cam_data['prototype_id']}")
            
        except Exception as e:
            print(f"Error enviando datos a RabbitMQ: {e}")