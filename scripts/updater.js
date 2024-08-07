
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

function waitForCondition(conditionFunction) {
    return new Promise((resolve, reject) => {
        const interval = setInterval(() => {
            // console.log("Checking")
            if (conditionFunction()) {
                clearInterval(interval);
                resolve();
            }
        }, 200); // Check every 100 milliseconds
    });
}

// Example usage
function myCondition() {
    let s = document.querySelector("#modal > div > div > form > div.modal-body > div.custom-file.mb-3 > label")
    // Replace this with your actual condition
    return s !== null && s.textContent.endsWith(".csv\"")
}

function r(){
    document.querySelector("#table_wrapper > div > div.col.flex-grow-1 > div:nth-child(2) > div:nth-child(1) > div > button.btn.btn-outline-primary.buttons-select-all > span > i").click()
    if (!document.querySelector("#removeset").disabled){
        document.querySelector("#removeset").click()
    }
    document.querySelector("#importCsvButton").click()
    sleep(500).then(() => {
        document.querySelector("#id_file").click()
    
        waitForCondition(myCondition).then(() => {
            console.log('Condition met! Continuing execution...');
            document.querySelector("#modal > div > div > form > div.modal-footer > button").click()
        });
    })

}
