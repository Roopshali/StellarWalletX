from imports import *

file_name = "accounts.json"


def load_json_from_file():
    try:
        with open(file_name, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File not found at path: {file_name}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None


def generate_accounts_json(new_name):
    try:
        # Load existing accounts data from the JSON file
        with open('accounts.json', 'r') as file:
            existing_accounts = json.load(file)

    except FileNotFoundError:
        # If the file doesn't exist, create an empty list
        existing_accounts = []

    # Generate a new key pair for the new account
    new_keypair = Keypair.random()

    # Create a new account dictionary
    new_account = {
        "name": new_name,
        "secret": new_keypair.secret,
        "publicKey": new_keypair.public_key
    }

    # Append the new account to the existing accounts data
    existing_accounts.append(new_account)

    # Write the updated accounts data back to the JSON file
    with open('accounts.json', 'w') as file:
        json.dump(existing_accounts, file, indent=4)

    print(f"Account for {new_name} added to JSON file.")
    return new_account  # Return the new account details

    # except Exception as e:
    #     print(f"Error generating account: {e}")
    #     return None


def fund_accounts():
    accounts = load_json_from_file()
    try:
        responses = []
        for account in accounts:
            response = requests.get(
                "https://horizon-testnet.stellar.org/friendbot",
                params={"addr": account["publicKey"]}
            )
            response_json = response.json()
            responses.append(response_json)
            st.balloons()
            st.header("Account Funded!")
            print(f"Account funded: {account['name']}")
        return responses
    except Exception as e:
        print(f"Error funding accounts: {e}")
        raise e


def check_accounts_balances(public_key):
    # Load accounts from the specified JSON file
    try:
        server = Server(horizon_url="https://horizon-testnet.stellar.org")
        s_accounts = []
        stellar_account = server.load_account(public_key)
        x = stellar_account.raw_data["balances"]
        print(x)
        transactions = []
        i = 1
        for transaction in x:
            balance_info = {
                "transaction no.": i,  # You can change this to the appropriate transaction identifier
                "balance": transaction["balance"],
                "buying_liabilities": transaction["buying_liabilities"],
                "selling_liabilities": transaction["selling_liabilities"],
                "asset_type": transaction["asset_type"]
            }
            i += 1
            transactions.append(balance_info)

        return transactions

    except Exception as e:
        st.error(f"Error checking account balances: {e}")
        raise e


def make_tx(source_amount, source_secret_key, destination_account_id):
    try:
        server = Server(horizon_url="https://horizon-testnet.stellar.org")
        source_keypair = Keypair.from_secret(source_secret_key)
        destination_keypair = Keypair.from_public_key(destination_account_id)

        source_account = server.load_account(
            account_id=source_keypair.public_key)
        base_fee = server.fetch_base_fee()

        transaction = TransactionBuilder(
            source_account=source_account,
            network_passphrase="Test SDF Network ; September 2015",
            base_fee=base_fee
        ).append_payment_op(
            destination=destination_keypair.public_key,
            amount=str(source_amount),
            asset=Asset.native()
        ).set_timeout(30).build()

        transaction.sign(source_keypair)
        response = server.submit_transaction(transaction)

        if isinstance(response, str):
            print(f"Error making transaction: {response}")
        else:
            print(f"Transaction Successful! Transaction Hash: {response['hash']}")
        
        return response
    except Exception as e:
        print(f"Error making transaction: {e}")
        return None


def get_account_names():
    accounts = load_json_from_file()
    return [account["name"] for account in accounts]


def get_account(name, sec):
    accounts = load_json_from_file()
    for account in accounts:
        if account["name"] == name and account["secret"] == sec:
            return account["name"], account["secret"], account["publicKey"]
    return "", "", ""


def main():
    st.session_state["logged_in"] = False
    st.title("Stellar Transaction App")
    st.sidebar.header("LOGIN")
    
    st.header("Create Accounts")
    name = st.text_input("Enter Account Name:")
    if st.button("Generate Account"):
        generated_account = generate_accounts_json(name)
        if generated_account:
            st.write("Account Created!")
            st.write("Name: ", generated_account["name"])
            st.write("Secret Key: ", generated_account["secret"])
            st.write("Public Key: ", generated_account["publicKey"])
    

    name = st.sidebar.text_input("Name", placeholder="Enter Name")
    sec = st.sidebar.text_input(
        "Enter Secret Key", placeholder="xxxx-xxxx-xxxx")
    button = st.sidebar.checkbox("Login")
    if sec and button:
        st.session_state["name"], st.session_state["secret"], st.session_state["publicKey"] = get_account(
            name, sec)
        if st.session_state["name"] != "":
            st.sidebar.success(f"Logged in as {st.session_state['name']}")
            st.session_state["logged_in"] = True
            if st.sidebar.button("Fund Accounts"):
                fund_accounts()
            if st.session_state["logged_in"]:
                if st.sidebar.button("Check Balances"):
                    with st.spinner("Fetching Balances..."):
                        balances = check_accounts_balances(
                            public_key=st.session_state["publicKey"])
                    st.success("Balances Fetched!")
                    if balances:
                        st.header("Account Balances")
                        df = pd.DataFrame(balances)
                        st.table(df)
                st.sidebar.header("Make Transaction")
                amount = st.number_input("Enter Amount:", min_value=0, step=1)
                destination_account_id = st.text_input(
                    "Enter Destination Account ID:")

                if st.button("Make Transaction"):
                    make_tx(
                        amount, st.session_state["secret"], destination_account_id)
                    if amount > 0 and destination_account_id:
                        response = make_tx(
                            amount, st.session_state["secret"], destination_account_id)
                        if response.get("hash"):
                            st.success(
                                f"Transaction Successful! Transaction Hash: {response['hash']}")
                        else:
                            st.error(
                                "Transaction Failed. Please check the provided details.")
                    else:
                        st.warning(
                            "Invalid Amount or Destination Account ID. Please provide valid inputs.")
                    st.write(
                        "Transaction Successful! Transaction Hash: 1234567890")
        else:
            st.sidebar.error("Invalid Credentials. Please try again.")


if __name__ == "__main__":
    main()
