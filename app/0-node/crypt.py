import os

from os import unlink
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP


class rsa_encrypter:

    _keysize = 2048

    def __init__(self, passphrase: str, session_key: str) -> None:
        self.session_key = session_key

        try:
            self.get_key(passphrase=passphrase, path='./RSA-keys')
            if not self.private_key or not self.public_key:
                exit(1)
        except ValueError as e:
            print(f"Invalid passphrase: {e.args[::-1]}")
            exit(1)
        except Exception as e:
            print(f"Unexpected error on fetching key: {e.args[::-1]}")
            exit(1)
        
        self.cipher_rsa_public = PKCS1_OAEP.new(self.public_key)
        self.cipher_rsa_private = PKCS1_OAEP.new(self.private_key)


    def get_key(self, passphrase: str, path: str='./RSA-keys'):
        if path and os.path.isfile(f'{path}/private.pem') and os.path.isfile(f'{path}/public.pem'):
            print(f'Using existing keypair..')
            try:
                with open(f'{path}/private.pem', 'r') as f:
                    self.private_key = RSA.importKey(extern_key=f.read(), passphrase=passphrase)
                with open(f'{path}/public.pem', 'r') as f:
                    self.public_key = RSA.importKey(extern_key=f.read(), passphrase=passphrase)
            except ValueError as e:
                print(f'Invalid RSA key: {e.args[::-1]}')
                return None
            except Exception as e:
                print(f'Error fetching RSA key: {e.args[::-1]}')
                return None
            
        else:
            print(f'Generating new directory..')
            try:
                os.mkdir(path=path)
            except Exception as e:
                print(f"Error creating directory: {e.args[::-1]}")
                return None
            
            print(f'Generating new keypair..')
            self.private_key = RSA.generate(self._keysize)

            with open(f'{path}/private.pem', 'wb') as f:
                f.write(self.private_key.exportKey(passphrase=passphrase, pkcs=8))
            with open(f'{path}/public.pem', 'wb') as f:
                f.write(self.private_key.publickey().exportKey(passphrase=passphrase, pkcs=8))
            # init public key
            with open(f'{path}/public.pem', 'rb') as f:
                self.public_key = RSA.importKey(extern_key=f.read(), passphrase=passphrase)


    def encrypt(self, mode: str='public'):
        if mode == 'private':
            return self.cipher_rsa_private.encrypt(self.session_key)
        else:
            return self.cipher_rsa_public.encrypt(self.session_key)


    def decrypt(self, mode: str='private'):
        file_in = open("encrypted_data.bin", "rb")

        if mode == 'private':
            enc_session_key, nonce, tag, ciphertext = \
                [ file_in.read(x) for x in (self.private_key.size_in_bytes(), 16, 16, -1) ]
            decrypted_session_key = self.cipher_rsa_private.decrypt(enc_session_key)
        else:
            enc_session_key, nonce, tag, ciphertext = \
                [ file_in.read(x) for x in (self.public_key.size_in_bytes(), 16, 16, -1) ]
            decrypted_session_key = self.cipher_rsa_public.decrypt(enc_session_key)

        return decrypted_session_key, nonce, tag, ciphertext



class aes_encrypter:

    def __init__(self, passphrase: str) -> None:
        self.session_key = get_random_bytes(16)
        self.rsa_encrypter = rsa_encrypter(passphrase, self.session_key)
        self.cipher_aes = AES.new(self.session_key, AES.MODE_EAX)


    def encrypt(self, data) -> int:
        enc_session_key = self.rsa_encrypter.encrypt('public')
        ciphertext, tag = self.cipher_aes.encrypt_and_digest(data)

        file_out = open("encrypted_data.bin", "wb")
        [ file_out.write(x) for x in (enc_session_key, self.cipher_aes.nonce, tag, ciphertext) ]
        file_out.close()

        print(f"DEBUG 0:\r\ntag: {tag}\r\nnonce: {self.cipher_aes.nonce}\r\nciphertext: {ciphertext}\r\nenc_session_key: {enc_session_key}\r\n")

        return 0


    def decrypt(self):
        decrypted_session_key, nonce, tag, ciphertext = self.rsa_encrypter.decrypt('private')
        temp_cipher_aes = AES.new(decrypted_session_key, AES.MODE_EAX, nonce)

        print(f"DEBUG 1:\r\ntag: {tag}\r\nnonce: {nonce}\r\nciphertext: {ciphertext}\r\ndecrypted_session_key: {decrypted_session_key}\r\n")

        data = temp_cipher_aes.decrypt_and_verify(ciphertext, tag)
        return data



if __name__ == '__main__':

    data = "We attack at dawn..".encode("utf-8")

    passphrase = input('Enter passphrase: ')

    crypt = aes_encrypter(passphrase)

    crypt.encrypt(data)
    decrypted = crypt.decrypt()

    print(f"{decrypted.decode()}\r\n")