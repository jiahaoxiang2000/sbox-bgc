#!/usr/bin/env python3
"""
S-box to SMT2 Generator

This script generates SMT2 files from S-box definitions for solving with STP.
It uses Bitwuzla to construct the SMT problem and exports it to SMT2 format.
"""

from bitwuzla import TermManager, Options, Option, Bitwuzla, Kind
import argparse
import sys
import os


def sbox_to_bits(sbox: list, bits: int = 4) -> list:
    """
    Convert S-box values to bit representation.

    Args:
        sbox: List of S-box values (e.g., [4, 7, 9, 11, ...])
        bits: Number of bits (3 or 4)

    Returns:
        List of integers representing the bit columns of the S-box
    """
    ys = [0] * bits
    for i in range(len(sbox)):
        for bit_pos in range(bits):
            ys[bits - 1 - bit_pos] = ys[bits - 1 - bit_pos] | (
                ((sbox[i] >> bit_pos) & 1) << (len(sbox) - 1 - i)
            )
    return ys


def generate_smt2_from_sbox(
    sbox: list, output_file: str, bits: int = 4, gate_number: int = 20
):
    """
    Generate SMT2 file from S-box definition.

    Args:
        sbox: S-box as list of integers
        output_file: Path to output SMT2 file
        bits: Number of input/output bits (default: 4)
        gate_number: Number of gates to use (default: 20)
    """
    # Convert S-box to bit representation
    ys = sbox_to_bits(sbox, bits)

    # Generate input pattern based on bit size
    if bits == 3:
        # For 3-bit S-boxes: [0b11110000, 0b11001100, 0b10101010]
        xs = [0xF0, 0xCC, 0xAA]  # 8-bit patterns for 3-bit inputs
    elif bits == 4:
        # For 4-bit S-boxes: [0b1111111100000000, 0b1111000011110000, 0b1100110011001100, 0b1010101010101010]
        xs = [0x00FF, 0x0F0F, 0x3333, 0x5555]  # 16-bit patterns for 4-bit inputs
    else:
        raise ValueError(
            f"Unsupported bit size: {bits}. Only 3 and 4 bits are supported."
        )

    print(f"S-box: {sbox}")
    print(f"Bits: {bits}")
    print(f"Input bits (xs): {[hex(x) for x in xs]}")
    print(f"Output bits (ys): {[hex(y) for y in ys]}")

    # Initialize Bitwuzla
    tm = TermManager()
    options = Options()
    options.set(Option.PRODUCE_MODELS, True)
    bitwuzla = Bitwuzla(tm, options)

    # Create bit vector sort
    bit_width = 2**bits
    sortbv = tm.mk_bv_sort(bit_width)

    # Gate types: XOR, AND, OR, NOT
    gts = [0b0110, 0b0001, 0b0111, 0b1100]

    # Create input and output variables
    xs_v = [tm.mk_const(sortbv, f"x{i}") for i in range(bits)]
    ys_v = [tm.mk_const(sortbv, f"y{i}") for i in range(bits)]

    # Create constraints for inputs
    for i in range(bits):
        bitwuzla.assert_formula(
            tm.mk_term(Kind.EQUAL, [xs_v[i], tm.mk_bv_value(sortbv, xs[i])])
        )

    # Create constraints for outputs
    for i in range(bits):
        bitwuzla.assert_formula(
            tm.mk_term(Kind.EQUAL, [ys_v[i], tm.mk_bv_value(sortbv, ys[i])])
        )

    # Create gate variables
    ts_v = [tm.mk_const(sortbv, f"t{i}") for i in range(gate_number)]
    qs_v = [tm.mk_const(sortbv, f"q{i}") for i in range(gate_number * 2)]
    gts_v = [tm.mk_const(sortbv, f"gt{i}") for i in range(gate_number)]

    # Create constraints for gate inputs
    for i in range(gate_number):
        input0 = [tm.mk_term(Kind.EQUAL, [qs_v[2 * i], xs_v[j]]) for j in range(bits)]
        input1 = [
            tm.mk_term(Kind.EQUAL, [qs_v[2 * i + 1], xs_v[j]]) for j in range(bits)
        ]
        inter0 = [tm.mk_term(Kind.EQUAL, [qs_v[2 * i], ts_v[j]]) for j in range(i)]
        inter1 = [tm.mk_term(Kind.EQUAL, [qs_v[2 * i + 1], ts_v[j]]) for j in range(i)]
        bitwuzla.assert_formula(tm.mk_term(Kind.OR, input0 + inter0))
        bitwuzla.assert_formula(tm.mk_term(Kind.OR, input1 + inter1))

    # Create constraints for gate types
    for i in range(gate_number):
        types = [
            tm.mk_term(Kind.EQUAL, [gts_v[i], tm.mk_bv_value(sortbv, gts[j])])
            for j in range(len(gts))
        ]
        bitwuzla.assert_formula(tm.mk_term(Kind.OR, types))

    # Create gate output constraints
    one_sort = tm.mk_bv_sort(1)
    one = tm.mk_bv_value(one_sort, 1)
    zeros = tm.mk_bv_value(sortbv, 0)
    ones = tm.mk_bv_value(sortbv, 2**bit_width - 1)

    for i in range(gate_number):
        # Extract gate type bits
        gt0 = tm.mk_term(Kind.BV_EXTRACT, [gts_v[i]], [0, 0])
        gt1 = tm.mk_term(Kind.BV_EXTRACT, [gts_v[i]], [1, 1])
        gt2 = tm.mk_term(Kind.BV_EXTRACT, [gts_v[i]], [2, 2])
        gt3 = tm.mk_term(Kind.BV_EXTRACT, [gts_v[i]], [3, 3])

        # Create conditional logic for each gate type bit
        gt0_ul = tm.mk_term(
            Kind.ITE,
            [
                tm.mk_term(Kind.BV_ULT, [gt0, one]),
                zeros,
                tm.mk_term(Kind.BV_AND, [qs_v[2 * i], qs_v[2 * i + 1]]),
            ],
        )
        gt1_ul = tm.mk_term(
            Kind.ITE,
            [
                tm.mk_term(Kind.BV_ULT, [gt1, one]),
                zeros,
                qs_v[2 * i + 1],
            ],
        )
        gt2_ul = tm.mk_term(
            Kind.ITE,
            [
                tm.mk_term(Kind.BV_ULT, [gt2, one]),
                zeros,
                qs_v[2 * i],
            ],
        )
        gt3_ul = tm.mk_term(
            Kind.ITE,
            [
                tm.mk_term(Kind.BV_ULT, [gt3, one]),
                zeros,
                ones,
            ],
        )

        # Assert gate output equation
        bitwuzla.assert_formula(
            tm.mk_term(
                Kind.EQUAL,
                [
                    ts_v[i],
                    tm.mk_term(
                        Kind.BV_XOR,
                        [
                            gt0_ul,
                            tm.mk_term(
                                Kind.BV_XOR,
                                [gt1_ul, tm.mk_term(Kind.BV_XOR, [gt2_ul, gt3_ul])],
                            ),
                        ],
                    ),
                ],
            )
        )

    # Create constraints linking outputs to gate outputs
    for i in range(bits):
        ts_temp = [
            tm.mk_term(Kind.EQUAL, [ys_v[i], ts_v[j]]) for j in range(gate_number)
        ]
        bitwuzla.assert_formula(tm.mk_term(Kind.OR, ts_temp))

    # Generate SMT2 string
    smt2_content = bitwuzla.print_formula()

    # Add (get-model) command before (exit) if not present
    if "(get-model)" not in smt2_content:
        # Replace (exit) with (get-model)\n(exit)
        smt2_content = smt2_content.replace("(exit)", "(get-model)\n(exit)")

    # Write to file
    with open(output_file, "w") as f:
        f.write(smt2_content)

    print(f"SMT2 file generated: {output_file}")
    return smt2_content


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(
        description="Generate SMT2 files from S-box definitions"
    )
    parser.add_argument(
        "--sbox",
        type=str,
        required=True,
        help='S-box as comma-separated values (e.g., "4,7,9,11,12,6,14,15,0,5,1,13,8,3,2,10" for 4-bit or "3,4,6,1,2,0,7,5" for 3-bit)',
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Output SMT2 file path"
    )
    parser.add_argument(
        "--bits",
        type=int,
        default=4,
        help="Number of input/output bits: 3 or 4 (default: 4)",
    )
    parser.add_argument(
        "--gates", type=int, default=20, help="Number of gates to use (default: 20)"
    )

    args = parser.parse_args()

    # Parse S-box
    try:
        sbox = [int(x.strip()) for x in args.sbox.split(",")]
        if len(sbox) != 2**args.bits:
            raise ValueError(
                f"S-box must have {2**args.bits} elements for {args.bits}-bit inputs"
            )
    except ValueError as e:
        print(f"Error parsing S-box: {e}")
        sys.exit(1)

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Generate SMT2 file
    try:
        generate_smt2_from_sbox(sbox, args.output, args.bits, args.gates)
        print(f"Successfully generated {args.output}")
    except Exception as e:
        print(f"Error generating SMT2 file: {e}")
        sys.exit(1)


# Predefined S-boxes for easy access
PREDEFINED_SBOXES = {
    # 4-bit S-boxes
    "default": [4, 7, 9, 11, 12, 6, 14, 15, 0, 5, 1, 13, 8, 3, 2, 10],
    "inverse": [8, 10, 14, 13, 0, 9, 5, 1, 12, 2, 15, 3, 4, 11, 6, 7],
    "midori": [
        0xC,
        0xA,
        0xD,
        0x3,
        0xE,
        0xB,
        0xF,
        0x7,
        0x8,
        0x9,
        0x1,
        0x5,
        0x0,
        0x2,
        0x4,
        0x6,
    ],
    # 3-bit S-boxes
    "3bit_example1": [3, 4, 6, 1, 2, 0, 7, 5],  # Example 3-bit S-box
    "3bit_example2": [1, 2, 4, 7, 3, 6, 0, 5],  # Another 3-bit S-box
}


if __name__ == "__main__":
    # If no arguments provided, show usage examples
    if len(sys.argv) == 1:
        print("S-box to SMT2 Generator")
        print("Usage examples:")
        print()
        print("1. Generate from command line:")
        print("   # 4-bit S-box")
        print(
            "   python sbox_to_smt2.py --sbox '4,7,9,11,12,6,14,15,0,5,1,13,8,3,2,10' --output smt2/custom.smt2"
        )
        print("   # 3-bit S-box")
        print(
            "   python sbox_to_smt2.py --sbox '3,4,6,1,2,0,7,5' --bits 3 --output smt2/custom_3bit.smt2"
        )
        print()
        print("2. Use predefined S-boxes:")
        for name, sbox in PREDEFINED_SBOXES.items():
            bits = 3 if len(sbox) == 8 else 4
            output_file = f"smt2/{name}.smt2"
            print(f"   # Generate {name} S-box ({bits}-bit)")
            sbox_str = ",".join(map(str, sbox))
            if bits == 3:
                print(
                    f"   python sbox_to_smt2.py --sbox '{sbox_str}' --bits 3 --output {output_file}"
                )
            else:
                print(
                    f"   python sbox_to_smt2.py --sbox '{sbox_str}' --output {output_file}"
                )
        print()
        print("3. Import as module:")
        print("   from sbox_to_smt2 import generate_smt2_from_sbox")
        print(
            "   generate_smt2_from_sbox([4,7,9,11,12,6,14,15,0,5,1,13,8,3,2,10], 'output.smt2', bits=4)"
        )
        print(
            "   generate_smt2_from_sbox([3,4,6,1,2,0,7,5], 'output_3bit.smt2', bits=3)"
        )
        sys.exit(0)

    main()
