function mainmenu(args) {

//01
if(args == "101") args = "/en/sub101.php";
if(args == "102") args = "/en/sub102.php";

//02
if(args == "201") args = "/en/sub201.php";
if(args == "202") args = "/en/sub202.php";

//03
if(args == "301") args = "/en/sub301.php";
if(args == "302") args = "/en/sub302.php";
if(args == "303") args = "/en/sub303.php";
if(args == "304") args = "/en/sub304.php";
if(args == "305") args = "/en/sub305.php";
if(args == "306") args = "/en/sub306.php";
if(args == "307") args = "/en/sub307.php";
if(args == "308") args = "/en/sub308.php";
if(args == "309") args = "/en/sub309.php";
if(args == "310") args = "/en/sub310.php";
if(args == "311") args = "/en/sub311.php";
if(args == "312") args = "/en/sub312.php";
if(args == "313") args = "/en/sub313.php";
if(args == "314") args = "/en/sub314.php";
if(args == "315") args = "/en/sub315.php";
if(args == "316") args = "/en/sub316.php";
if(args == "321") args = "/sub321.php";

//04
if(args == "401") args = "/gnuboard5/bbs/board.php?bo_table=sub401_en";
if(args == "402") args = "/gnuboard5/bbs/board.php?bo_table=sub402_en";


location.href = ""+ args;
}

function main() {  parent.location.href = "/en/" ; }