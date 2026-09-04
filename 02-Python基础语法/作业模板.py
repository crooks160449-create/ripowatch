"""作业模板：学生信息管理系统"""


class Student:
    """学生类"""

    def __init__(self, name: str, student_id: str, score: float = 0.0):
        self.name = name
        self.student_id = student_id
        self.score = score

    def __str__(self):
        return f"{self.name} ({self.student_id}): {self.score} 分"


class StudentManager:
    """学生管理器"""

    def __init__(self):
        self.students: list[Student] = []

    def add_student(self, name: str, student_id: str, score: float = 0.0):
        """添加学生"""
        self.students.append(Student(name, student_id, score))
        print(f"已添加学生: {name}")

    def remove_student(self, student_id: str):
        """删除学生"""
        for s in self.students:
            if s.student_id == student_id:
                self.students.remove(s)
                print(f"已删除学生: {s.name}")
                return
        print(f"未找到学号为 {student_id} 的学生")

    def list_students(self):
        """列出所有学生"""
        if not self.students:
            print("暂无学生信息")
            return
        print(f"\n{'='*40}")
        print(f"{'姓名':<10} {'学号':<12} {'成绩':>6}")
        print(f"{'-'*40}")
        for s in sorted(self.students, key=lambda x: x.score, reverse=True):
            print(f"{s.name:<10} {s.student_id:<12} {s.score:>6.1f}")
        print(f"{'='*40}\n")

    def get_average_score(self) -> float:
        """计算平均分"""
        if not self.students:
            return 0.0
        return sum(s.score for s in self.students) / len(self.students)


# ============================================================
# 作业要求：
# 1. 补全 StudentManager 的 search_by_name 方法
# 2. 补全 StudentManager 的 update_score 方法
# 3. 补全 get_top_students 方法（返回前 N 名学生）
# 4. 在 main() 中测试你的实现
# ============================================================


def main():
    manager = StudentManager()

    # 添加测试数据
    manager.add_student("张三", "2024001", 85.5)
    manager.add_student("李四", "2024002", 92.0)
    manager.add_student("王五", "2024003", 78.5)

    # 列出所有学生
    manager.list_students()

    # 计算平均分
    avg = manager.get_average_score()
    print(f"班级平均分: {avg:.1f}")


if __name__ == "__main__":
    main()
