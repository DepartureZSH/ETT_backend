import threading
import time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def start_training_thread():
    t = threading.Thread(target=train_loop, daemon=True)
    t.start()

def train_loop():
    channel_layer = get_channel_layer()
    print(channel_layer.__getstate__)
    for epoch in range(200):
        time.sleep(0.1)

        log = {
            "epoch": epoch,
            "loss": epoch * 0.01,
            "reward": 100 - epoch * 0.2,
        }
        # 广播给所有连接的前端
        async_to_sync(channel_layer.group_send)(
            "train_channel",
            {"type": "send_log", "data": log}
        )
