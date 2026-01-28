"""
Generate a cryptographic signature for a message using a Bittensor wallet.

This script signs a message with the wallet's coldkey and outputs a file
containing the original message, the signer's SS58 address, and the signature.
The output file can be verified using verify.py.

Usage:
    python generate.py --message "Your message here" --name your_wallet_name
    python generate.py --message "Your message here" --name your_wallet_name --output custom_output.txt
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import bittensor as bt


def generate_signature(wallet_name: str, message: str, output_file: str) -> bool:
    """
    Generate a cryptographic signature for a message using a Bittensor wallet.

    Args:
        wallet_name: Name of the Bittensor wallet to use for signing.
        message: The message to sign.
        output_file: Path to the output file where the signed message will be saved.

    Returns:
        True if signature was generated successfully, False otherwise.
    """
    try:
        # Load the wallet
        wallet = bt.wallet(name=wallet_name)
        keypair = wallet.coldkey
    except Exception as e:
        print(f"Error: Failed to load wallet '{wallet_name}': {e}")
        return False

    # Generate timestamp in ISO 8601 format with timezone
    timestamp = datetime.now(timezone.utc).isoformat()

    # Construct the message with timestamp
    full_message = f"[{timestamp}] {message}"

    try:
        # Sign the message
        signature = keypair.sign(data=full_message)
    except Exception as e:
        print(f"Error: Failed to sign message: {e}")
        return False

    # Format the output
    file_contents = (
        f"Message: {full_message}\n"
        f"Signed by: {keypair.ss58_address}\n"
        f"Signature: {signature.hex()}"
    )

    # Write to file
    output_path = Path(output_file)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(file_contents)
    except IOError as e:
        print(f"Error: Failed to write to file '{output_file}': {e}")
        return False

    print(file_contents)
    print(f"\nSignature generated and saved to: {output_path.absolute()}")
    return True


def main():
    """Parse arguments and generate signature."""
    parser = argparse.ArgumentParser(
        description="Generate a cryptographic signature for a message using a Bittensor wallet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python generate.py --message "Hello, Bittensor!" --name default
    python generate.py --message "Important announcement" --name my_wallet --output announcement.txt
        """,
    )
    parser.add_argument(
        "--message",
        type=str,
        required=True,
        help="The message to sign",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="default",
        help="The wallet name (default: 'default')",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="message_and_signature.txt",
        help="Output file path (default: 'message_and_signature.txt')",
    )

    args = parser.parse_args()

    success = generate_signature(
        wallet_name=args.name,
        message=args.message,
        output_file=args.output,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
