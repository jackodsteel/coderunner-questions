"""
The template for a question type in which a student submits a fully valid JUnit 5 test class in the answer box,
and the question author supplies a set of versions of the same model class that are expected to be valid/invalid,
as indicated by the expected result being PASS/FAIL.
The question compiles the student JUnit test class and model class and then uses JUnit Console Launcher to run the
given JUnit test class against the model class, and uses the return code to verify if the result was as expected.
"""

import json
import os
import re
import subprocess
from typing import Tuple

JUNK_JUNIT_OUTPUT_TEXT = "Thanks for using JUnit! Support its development at https://junit.org/sponsoring"

JUNIT_CONSOLE_FILE = "junit-platform-console-standalone-1.5.2.jar"


class TestingError(Exception):
    """
    Simple error class that has an accompanying message of what went wrong.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


def save_to_file(filename, body) -> None:
    with open(filename, "w") as src:
        print(body, file=src)


def run_process_to_stdout(arg: str):
    return subprocess.run(
        arg,
        universal_newlines=True,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )


class JUnitTester:

    def __init__(self, junit_console_file: str, junk_junit_output_text: str):
        self.junit_console_file = junit_console_file
        self.junk_junit_output_text = junk_junit_output_text
        self.class_detector_regex = re.compile(r'public\s+class\s+(\w+)')
        self._files_to_remove = set()

    def cleanup(self) -> None:
        for file in self._files_to_remove:
            os.remove(file)

    def test_junit_program(self,
                           model_class_code: str,
                           student_junit_code: str,
                           should_pass: bool,
                           is_precheck: bool
                           ) -> str:
        """
        Main program - compile all supplied Java files and run all JUnit tests

        :param model_class_code: The model code to use
        :param student_junit_code: The JUnit test class to use
        :param should_pass: if the test cases should pass or at least one should fail
        :param is_precheck: if True, don't run tests, just do compilation
        :return: A string with the output text
        :raise TestingError: if there were any issues with the student code that should result in a zero mark
        """

        # 1. Take given model class and save to file

        model_class_name = self.get_class_name_from_code(model_class_code, "model")
        save_to_file(f"{model_class_name}.java", model_class_code)
        self._files_to_remove.add(f"{model_class_name}.java")

        # 2. Compile saved model class

        compile_result = run_process_to_stdout(
            f"javac {model_class_name}.java"
        )
        if compile_result.returncode != 0:
            raise TestingError(compile_result.stdout + "\n** Compilation of model code failed. Testing aborted **")
        self._files_to_remove.add(f"{model_class_name}.class")

        # 3. Take given student JUnit code from STUDENT_ANSWER and save to file

        junit_class_name = self.get_class_name_from_code(student_junit_code, "JUnit")
        save_to_file(f"{junit_class_name}.java", student_junit_code)
        self._files_to_remove.add(f"{junit_class_name}.java")

        # 4. Compile student JUnit code

        compile_result = run_process_to_stdout(
            f"javac -cp .:{self.junit_console_file} {junit_class_name}.java"
        )
        if compile_result.returncode != 0:
            raise TestingError(f"{compile_result.stdout}\n** Compilation of JUnit code failed. Testing aborted **")
        self._files_to_remove.add(f"{junit_class_name}.class")

        # If precheck, return OK now, as we only want to make sure their code compiles.

        if is_precheck:
            return "** Code compiled successfully **"

        # 5. Run java -jar ConsoleRunner and save output

        execution_result = run_process_to_stdout(
            f"java -jar {self.junit_console_file} --details none --classpath . --select-class {junit_class_name}"
        )

        result_str = execution_result.stdout.replace(self.junk_junit_output_text, "").strip()

        # 6. Assert that the result was as expected

        if should_pass and execution_result.returncode == 1:
            raise TestingError(f"{result_str}\n\n** Expected the tests to pass, but at least one failed! **")
        if should_pass is False and execution_result.returncode == 0:
            raise TestingError(f"{result_str}\n\n** Expected at least one test to fail, but they all passed! **")
        if result_str == "" and execution_result.returncode == 0:
            result_str = "All tests passed!"

        return result_str

    def get_class_name_from_code(self, code: str, code_type: str) -> str:
        """
        :param code: The source code to extract the class name from
        :param code_type: The type of code to be used for error messages
        :return: The class name found
        :raise TestingError: if there was not exactly one valid class
        """
        class_name_search = self.class_detector_regex.search(code)
        if class_name_search is None:
            raise TestingError(f"** Could not find public class in the {code_type} code. Testing aborted **")
        if len(class_name_search.groups()) > 1:
            raise TestingError(f"** Multiple public classes found in the {code_type} code. Testing aborted **")
        return class_name_search.group(1)

    @staticmethod
    def parse_args(model_class_code_str: str,
                   student_junit_code_str: str,
                   expected_result_str: str,
                   is_precheck_str: str
                   ) -> Tuple[str, str, bool, bool]:
        """
        Take the arguments from the template input and parse them. Do some validation to check values are valid

        :return: 4 tuple with the model code, student code, if the tests should pass or fail,
         and if the test is a precheck
        :raise TestingError: if the inputs do not match the required input
        """
        if is_precheck_str not in ("0", "1"):
            raise TestingError("IS_PRECHECK must be 0 or 1")
        is_precheck = True if (is_precheck_str == "1") else False
        if expected_result_str not in ("PASS", "FAIL"):
            raise TestingError("Expected output must be either PASS or FAIL")
        should_pass = True if expected_result_str == "PASS" else False
        return model_class_code_str, student_junit_code_str, should_pass, is_precheck


def run_tester():
    """
    Tries to run main_logic but catches any TestingErrors gracefully.
    Prints the JSON data as expected by the CodeRunner test executor.
    """
    is_precheck_str = """{{ IS_PRECHECK }}"""
    expected_result_str = """{{ TEST.expected }}"""
    model_class_code_str = """{{ TEST.testcode | e('py') }}"""
    student_junit_code_str = """{{ STUDENT_ANSWER | e('py') }}"""

    junit_tester = JUnitTester(JUNIT_CONSOLE_FILE, JUNK_JUNIT_OUTPUT_TEXT)
    try:
        model_class_code, student_junit_code, should_pass, is_precheck = junit_tester.parse_args(
            model_class_code_str, student_junit_code_str, expected_result_str, is_precheck_str)
        output_text = junit_tester.test_junit_program(model_class_code, student_junit_code, should_pass, is_precheck)
        fractional_score = 1
    except TestingError as e:
        output_text = e.message
        fractional_score = 0
    finally:
        junit_tester.cleanup()
    result = {'fraction': fractional_score, 'got': output_text}
    print(json.dumps(result))


if __name__ == "__main__":
    run_tester()
