from preconditions import SystemPreconditions

class ConfigurationError(Exception):
    pass

# pre = SystemPreconditions.load_settings("/home/pals/code/config/settings.json")

pre = SystemPreconditions()

print(pre.check())

print(pre.check_desired_state())