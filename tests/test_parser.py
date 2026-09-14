from app.parser.log_parser import LogParser

parser = LogParser()

stack_trace = """
java.lang.NullPointerException

at LoginService.java:45

at UserController.java:18
"""

print(parser.parse(stack_trace))
