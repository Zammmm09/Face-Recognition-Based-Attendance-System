<?php
// Enable full error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Log all activities
file_put_contents('mailer.log', date('[Y-m-d H:i:s] ')."Script started\n", FILE_APPEND);

function log_message($message) {
    file_put_contents('mailer.log', date('[Y-m-d H:i:s] ').$message."\n", FILE_APPEND);
}

// Load PHPMailer
require __DIR__.'/PHPMailer/PHPMailer.php';
require __DIR__.'/PHPMailer/SMTP.php';
require __DIR__.'/PHPMailer/Exception.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\SMTP;
use PHPMailer\PHPMailer\Exception;

header('Content-Type: application/json');

try {
    // Get input data
    $json = file_get_contents('php://input');
    $data = json_decode($json, true);
    
    if (!$data || !isset($data['student'])) {
        throw new Exception("Invalid request: Student name missing");
    }

    $student = trim($data['student']);
    $subject = isset($data['subject']) ? trim($data['subject']) : 'General';
    
    // Find parent email
    $students = file(__DIR__.'/students.txt', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $parent_email = null;
    
    foreach ($students as $line) {
        list($name, $email) = explode(',', $line, 2);
        if (trim($name) === $student) {
            $parent_email = trim($email);
            break;
        }
    }
    
    if (!$parent_email) {
        throw new Exception("Parent email not found for: $student");
    }

    // Configure PHPMailer
    $mail = new PHPMailer(true);
    $mail->isSMTP();
    $mail->Host = 'smtp.gmail.com';
    $mail->SMTPAuth = true;
    $mail->Username = 'attendifysupp@gmail.com';
    $mail->Password = 'zqwc xrhz zsyy kqtp';
    $mail->SMTPSecure = PHPMailer::ENCRYPTION_SMTPS;
    $mail->Port = 465;

    $mail->setFrom('attendifysupp@gmail.com', 'Attendify System');
    $mail->addAddress($parent_email);
    $mail->Subject = "Attendance Notification: $subject";
    $mail->Body = "
        <h2>Attendance Confirmation</h2>
        <p>Student: <strong>$student</strong></p>
        <p>Subject: <strong>$subject</strong></p>
        <p>Status: <span style='color:green;'>Present</span></p>
        <p>Date: ".date('Y-m-d H:i:s')."</p>
    ";
    $mail->isHTML(true);

    $mail->send();
    log_message("Email sent to $parent_email for $student");
    echo json_encode(['success' => true]);
    
} catch (Exception $e) {
    log_message("ERROR: ".$e->getMessage());
    echo json_encode([
        'success' => false,
        'message' => $e->getMessage()
    ]);
}
?>