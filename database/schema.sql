-- Internal Assessment Marks Management System - Database Schema

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL,
    course_name TEXT NOT NULL,
    subject_code TEXT NOT NULL,
    department TEXT NOT NULL,
    semester TEXT NOT NULL,
    total_co INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS course_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    co_number INTEGER NOT NULL,
    co_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    reg_no TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE(course_id, reg_no)
);

CREATE TABLE IF NOT EXISTS internals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    internal_name TEXT NOT NULL,
    assignment_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS internal_co_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    internal_id INTEGER NOT NULL,
    co_number INTEGER NOT NULL,
    max_marks REAL DEFAULT 10,
    FOREIGN KEY (internal_id) REFERENCES internals(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assignment_structure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    internal_id INTEGER NOT NULL,
    assignment_number INTEGER NOT NULL,
    max_marks REAL NOT NULL,
    FOREIGN KEY (internal_id) REFERENCES internals(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    internal_id INTEGER NOT NULL,
    component_type TEXT NOT NULL CHECK (component_type IN ('CO', 'ASSIGNMENT')),
    component_number INTEGER NOT NULL,
    marks REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (internal_id) REFERENCES internals(id) ON DELETE CASCADE,
    UNIQUE(student_id, internal_id, component_type, component_number)
);

CREATE INDEX IF NOT EXISTS idx_courses_teacher ON courses(teacher_id);
CREATE INDEX IF NOT EXISTS idx_students_course ON students(course_id);
CREATE INDEX IF NOT EXISTS idx_internals_course ON internals(course_id);
CREATE INDEX IF NOT EXISTS idx_internal_co_mapping_internal_id ON internal_co_mapping(internal_id);
CREATE INDEX IF NOT EXISTS idx_assignment_structure_internal_id ON assignment_structure(internal_id);
CREATE INDEX IF NOT EXISTS idx_marks_student_id ON marks(student_id);
CREATE INDEX IF NOT EXISTS idx_marks_internal_id ON marks(internal_id);
CREATE INDEX IF NOT EXISTS idx_marks_student_internal ON marks(student_id, internal_id);

-- Default teacher account
INSERT OR IGNORE INTO users (teacher_id, name, password) VALUES ('TCH001', 'Faculty', 'faculty123');
<<<<<<< HEAD

CREATE TABLE IF NOT EXISTS co_po_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    co_number INTEGER NOT NULL,
    po_name TEXT NOT NULL,
    correlation_level INTEGER NOT NULL CHECK (correlation_level IN (1, 2, 3)),
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE(course_id, co_number, po_name)
);

CREATE TABLE IF NOT EXISTS co_attainment_config (
    course_id INTEGER NOT NULL,
    co_number INTEGER NOT NULL,
    ese_marks REAL DEFAULT 0,
    ida_level REAL DEFAULT 0,
    UNIQUE(course_id, co_number)
);

CREATE TABLE IF NOT EXISTS da_level_config (
    course_id INTEGER PRIMARY KEY,
    level_3 REAL DEFAULT 85,
    level_2 REAL DEFAULT 75,
    level_1 REAL DEFAULT 60
);

CREATE TABLE IF NOT EXISTS ese_marks (
    course_id INTEGER,
    student_id INTEGER,
    marks REAL,
    PRIMARY KEY(course_id, student_id)
);

CREATE TABLE IF NOT EXISTS grade_mapping (
    course_id INTEGER,
    grade TEXT,
    marks_equivalent REAL,
    PRIMARY KEY(course_id, grade)
);
=======
>>>>>>> 71b952933dd2e916d4ac15410368dac0fb591c05
