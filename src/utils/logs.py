from datetime import datetime


def log(level, tag, message, **fields):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    args = " ".join([f"{k}={v}" for k, v in fields.items()])
    suffix = f" {args}" if args else ""
    print(f"{timestamp} [{level.upper()}] {tag.upper()} {message}{suffix}")

def info(tag, message, **fields):
    log("✅ INFO", tag, message, **fields)

def warn(tag, message, **fields):
    log("⚠️ WARN", tag, message, **fields)

def error(tag, message, **fields):
    log("❌ ERROR", tag, message, **fields)

def debug(tag, message, **fields):
    log("🔧 DEBUG", tag, message, **fields)