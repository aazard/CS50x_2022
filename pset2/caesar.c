// Jeffrey Witty
// 12 August 2022
// Problem Set 2 - Encrypt messages using Caesar’s cipher
#include <stdlib.h>
#include <cs50.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

/*
 * Caesar.c
 * A program that encrypts messages using Caesar’s cipher. Your program must
 * accept a single command-line argument: a non-negative integer. If your program
 * is execute without any command-line arguments or with more than one command-line argument,
 * your program should tell the user and return a value of 1.
 *
 */

char rotate(char c, int n);

int main(int argc, string argv[])
{
    // Checks if argc 2 strings and argv second value is a digit
    if (argc == 2 && isdigit(*argv[1]))
    {
        // iterate through the argv
        for (int k = 0; k < strlen(argv[1]); k++)
        {
            // return 1 if there is non-digit value in argv
            if (!isdigit(argv[1][k]))
            {
                printf("Usage: ./caesar key\n");
                return 1;
            }
        }

        // turns argv into an integer value
        int i = atoi(argv[1]);

        // checks if that integer value us negative or zero
        if (i <= 0)
        {
            printf("Usage: ./caesar key\n");
            return 0;
        }
        else
        {
            // Get input text as plaintext
            string plaintext = get_string("plaintext: ");

            int n = strlen(plaintext);
            char ciphertext[n];

            // iterate through the plaintext and turn them into ciphertext
            printf("ciphertext: ");
            for (int j = 0; j < n; j++)
            {
                ciphertext[j] = rotate(plaintext[j], i);
                printf("%c", ciphertext[j]);
            }
            printf("\n");
        }
    }
    else
    {
        printf("Usage: ./caesar key\n");
        return 1;
    }
}


// this function takes a character and integer and shifts the character by the amount of the integer
char rotate(char c, int n)
{
    char cipher;

    if (islower(c))
    {
        cipher = (((c + n) - 97) % 26) + 97;
    }
    else if (isupper(c))
    {
        cipher = (((c + n) - 65) % 26) + 65;
    }
    else
    {
        cipher = c;
    }

    return cipher;
}