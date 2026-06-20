"""MQTT command handling utilities"""
from utils import mqtt
from utils import log
from utils import status as status_module
from utils.blink import blink
from utils.control import restart
from utils.timeutils import strftime, uptime

# Command registry - maps command names to handler functions
_command_handlers = {}
_custom_topic_handlers = {}

def register_command(command_name, handler_func):
    """Register a command handler function"""
    _command_handlers[command_name] = handler_func

def register_topic_handler(topic_pattern, handler_func):
    """Register a custom topic handler function"""
    _custom_topic_handlers[topic_pattern] = handler_func

def handle_blink(pico, timeInit): # pylint: disable=unused-argument
    """Handle blink command"""
    log.status("blinking")
    blink(0.1, 0.1, 5)

def handle_restart(pico, timeInit): # pylint: disable=unused-argument
    """Handle restart command"""
    log.status("Restarting")
    restart("mqtt command")

def handle_datetime(pico, timeInit): # pylint: disable=unused-argument
    """Handle datetime command"""
    thetime = strftime()
    log.status(f"Time is: {thetime}")

def handle_uptime(pico, timeInit): # pylint: disable=unused-argument
    """Handle uptime command"""
    log.status(f"Uptime: {uptime(timeInit)}")

def handle_temperature(pico, timeInit): # pylint: disable=unused-argument
    """Handle temperature command"""
    temperature = status_module.read_internal_temperature()
    temp_topic = f"temperature/{pico}"
    mqtt.send_mqtt(temp_topic, temperature)

def handle_clear(pico, timeInit): # pylint: disable=unused-argument
    """Handle clear command"""
    log.status("Clearing exception log")
    log.clear_log(pico)

def handle_status(pico, timeInit, get_status_func=None): # pylint: disable=unused-argument
    """Handle status command"""
    log.status(f"Uptime: {uptime(timeInit)}")
    log.status(f"My temperature: {status_module.read_internal_temperature()}C")
    if get_status_func:
        get_status_func()

def handle_heartbeat(pico, timeInit): # pylint: disable=unused-argument
    """Handle heartbeat poll"""
    heartbeat_topic = f"pico/{pico}/heartbeat"
    mqtt.send_mqtt(heartbeat_topic, "Yes, I'm here")

def handle_upload_log(pico, timeInit): # pylint: disable=unused-argument
    """Handle upload_log command to upload the exception log to the server"""
    log.status("Uploading exception log")
    log.upload_exceptions()

# Register default commands
def _init_default_commands():
    """Initialize default command handlers"""
    register_command("blink", handle_blink)
    register_command("restart", handle_restart)
    register_command("datetime", handle_datetime)
    register_command("uptime", handle_uptime)
    register_command("temperature", handle_temperature)
    register_command("clear", handle_clear)
    register_command("status", handle_status)
    register_command("upload_log", handle_upload_log)
# Initialize on module load
_init_default_commands()

def process_message(topic, payload, pico, timeInit, main_module=None):
    """Process incoming MQTT messages
    
    Args:
        topic: MQTT topic (bytes)
        payload: MQTT payload (bytes)
        pico: Pico identifier string
        timeInit: Initial time for uptime calculation
        main_module: Dynamically loaded pico-specific module (optional)
    """
    topic = str(topic.decode())
    payload = str(payload.decode())
    #log.debug(f"Received topic: {topic} message: {payload}")

    # Check if it's a control message for this pico or all picos
    if topic == f"pico/{pico}/control" or topic == "pico/all/control":
        command = payload

        # Look up command in registry
        if command in _command_handlers:
            handler = _command_handlers[command]
            if command == "status":
                # Special case: status command needs access to main module
                get_status_func = getattr(main_module, 'get_status', None) if main_module else None
                handler(pico, timeInit, get_status_func)
            else:
                handler(pico, timeInit)
        else:
            log.status(f"Unknown command: {payload}")

    # Check for heartbeat poll
    elif topic == "pico/poll":
        handle_heartbeat(pico, timeInit)

    # Check for custom topic handlers
    else:
        handled = False
        for topic_pattern, handler_func in _custom_topic_handlers.items():
            if topic_pattern in topic or topic == topic_pattern:
                handler_func(topic, payload)
                handled = True
                break

        # If not handled by custom handlers, try main module handlers
        if not handled and main_module:
            # Check for LED control topics
            if topic in ["pico/lights", "pico/xlights", "pico/plights"]:
                if hasattr(main_module, 'led_control'):
                    main_module.led_control(topic, payload)
            # Check for heartbeat (used by some picos)
            elif topic == "pico/pico2w0/heartbeat":
                if hasattr(main_module, 'heartbeat'):
                    main_module.heartbeat()
            elif topic == "pico/xbox":
                if hasattr(main_module, 'xbox_status'):
                    main_module.xbox_status(payload)
