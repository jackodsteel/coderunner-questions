import unittest
from PROTOTYPE_TEMPLATE_java_junit_tester_junit_5 import JUnitTester, TestingError


class MyTestCase(unittest.TestCase):

    JUNIT_CONSOLE_FILE = "junit-platform-console-standalone-1.5.2.jar"

    CORRECT_MODEL_CODE = """        
        public class User {
    
            private String username = "Default";
    
            public void setUsername(String username) {
                this.username = username;
            }
    
            public String getUsername() {
                return username;
            }
        }
    """

    INCORRECT_MODEL_CODE = """
        public class User {
    
            private String username = "Default";
    
            public void setUsername(String username) {
            }
    
            public String getUsername() {
                return username;
            }
        }
    """

    CORRECT_STUDENT_JUNIT_CODE = """
        import org.junit.jupiter.api.Test;

        import static org.junit.jupiter.api.Assertions.*;

        public class UserTest {

            @Test
            public void defaultUsernameTest() {
                User user = new User();
                assertEquals("Default", user.getUsername());
            }

            @Test
            public void getSetUsernameTest() {
                User user = new User();
                user.setUsername("Jack");
                assertEquals("Jack", user.getUsername());
            }

        }
    """

    NO_ASSERTIONS_STUDENT_JUNIT_CODE = """
        import org.junit.jupiter.api.Test;

        import static org.junit.jupiter.api.Assertions.*;

        public class UserTest {

            @Test
            public void defaultUsernameTest() {
            }

            @Test
            public void getSetUsernameTest() {
            }

        }
    """
    
    def setUp(self) -> None:
        self.sut = JUnitTester(self.JUNIT_CONSOLE_FILE, "")

    def tearDown(self) -> None:
        self.sut.cleanup()

    def test_valid_inputs_returns_correctly_when_pass_expected(self):
        self.sut.main_logic(self.CORRECT_MODEL_CODE, self.CORRECT_STUDENT_JUNIT_CODE, "PASS", False)

    def test_valid_inputs_raises_error_when_fail_expected(self):
        with self.assertRaises(TestingError):
            self.sut.main_logic(self.CORRECT_MODEL_CODE, self.CORRECT_STUDENT_JUNIT_CODE, "FAIL", False)

    def test_correct_junit_tests_returns_correctly_when_fail_expected_and_model_invalid(self):
        self.sut.main_logic(self.INCORRECT_MODEL_CODE, self.CORRECT_STUDENT_JUNIT_CODE, "FAIL", False)

    def test_correct_no_assertion_junit_tests_raises_error_when_fail_expected_and_model_invalid(self):
        with self.assertRaises(TestingError):
            self.sut.main_logic(self.INCORRECT_MODEL_CODE, self.NO_ASSERTIONS_STUDENT_JUNIT_CODE, "FAIL", False)

    def test_uncompilable_input_raises_error_when_pass_expected(self):
        with self.assertRaises(TestingError):
            self.sut.main_logic(self.CORRECT_MODEL_CODE, "not valid java;", "PASS", False)

    def test_uncompilable_input_raises_error_when_fail_expected(self):
        with self.assertRaises(TestingError):
            self.sut.main_logic(self.CORRECT_MODEL_CODE, "not valid java;", "FAIL", False)

    def test_uncompilable_input_raises_error_when_precheck_true(self):
        with self.assertRaises(TestingError):
            self.sut.main_logic(self.CORRECT_MODEL_CODE, "not valid java;", "FAIL", True)

    def test_non_fail_or_pass_expected_result_raises_error(self):
        with self.assertRaises(TestingError):
            self.sut.main_logic(self.CORRECT_MODEL_CODE, self.CORRECT_STUDENT_JUNIT_CODE, "SOMETHING_ELSE", False)

    def test_correct_no_assertion_junit_tests_returns_ok_when_fail_expected_and_model_invalid_but_precheck_true(self):
        self.sut.main_logic(self.CORRECT_MODEL_CODE, self.NO_ASSERTIONS_STUDENT_JUNIT_CODE, "FAIL", True)


if __name__ == '__main__':
    unittest.main()
