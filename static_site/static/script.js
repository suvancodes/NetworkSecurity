function validateForm() {
    const selects = document.querySelectorAll("select");
    for (let sel of selects) {
        if (sel.value === "") {
            alert("Please fill all fields.");
            return false;
        }
    }
    return true;
}