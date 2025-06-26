<?php
require 'PHPMailer/PHPMailer.php';
$mail = new PHPMailer(true);
$mail->isSMTP();
$mail->Host = 'smtp.gmail.com';
$mail->SMTPAuth = true;
$mail->Username = 'attendifysupp@gmail.com';
$mail->Password = 'zqwc xrhz zsyy kqtp';
$mail->SMTPSecure = 'ssl';
$mail->Port = 465;

if ($mail->smtpConnect()) {
    file_put_contents('mailer.log', "SMTP Connection Success!\n", FILE_APPEND);
    $mail->smtpClose();
    echo "SMTP Working!";
} else {
    file_put_contents('mailer.log', "SMTP Failed: ".$mail->ErrorInfo."\n", FILE_APPEND);
    echo "SMTP Failed: ".$mail->ErrorInfo;
}
?>