"""Secure Credential Storage Module.

This module provides functionality for securely storing and retrieving VPN credentials
using platform-specific mechanisms such as Windows Credential Manager, macOS Keychain,
Linux Secret Service API, and Android Keystore.
"""

import os
import sys
import json
import base64
import platform
from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod


class CredentialStorage(ABC):
    """Abstract base class for secure credential storage implementations."""
    
    @abstractmethod
    def store_credentials(self, service_name: str, credentials: Dict[str, str]) -> bool:
        if not service_name or not credentials.get('username') or not credentials.get('password'):
            raise ValueError("Missing required credential parameters")
        
        try:
            # Platform-specific storage implementation
            if sys.platform == 'win32':
                _windows_store_credentials(service_name, credentials['username'], credentials['password'])
            elif sys.platform == 'darwin':
                _macos_store_credentials(service_name, credentials['username'], credentials['password'])
            elif sys.platform.startswith('linux'):
                _linux_store_credentials(service_name, credentials['username'], credentials['password'])
            else:
                raise NotImplementedError("Unsupported platform for credential storage")
        except KeyringException as e:
            logger.error(f"Credential storage failed: {str(e)}")
            raise VPNCredentialError("Failed to store credentials") from e
        """Store credentials securely.
        
        Args:
            service_name: A unique identifier for the VPN service.
            credentials: Dictionary containing credentials to store.
        
        Returns:
            bool: True if credentials were stored successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    def retrieve_credentials(self, service_name: str) -> Optional[Dict[str, str]]:
        """Retrieve stored credentials.
        
        Args:
            service_name: The unique identifier for the VPN service.
        
        Returns:
            Optional[Dict[str, str]]: The stored credentials, or None if not found.
        """
        pass
    
    @abstractmethod
    def delete_credentials(self, service_name: str) -> bool:
        """Delete stored credentials.
        
        Args:
            service_name: The unique identifier for the VPN service.
        
        Returns:
            bool: True if credentials were deleted successfully, False otherwise.
        """
        pass


class WindowsCredentialStorage(CredentialStorage):
    """Windows-specific implementation using Windows Credential Manager."""
    
    def __init__(self):
        """Initialize the Windows credential storage."""
        try:
            import win32cred
            import win32credui
            self._win32cred = win32cred
            self._win32credui = win32credui
        except ImportError:
            raise ImportError("The 'pywin32' package is required for Windows credential storage.")
    
    def store_credentials(self, service_name: str, credentials: Dict[str, str]) -> bool:
        """Store credentials using Windows Credential Manager."""
        try:
            # Convert credentials to JSON and encode as bytes
            cred_blob = json.dumps(credentials).encode('utf-8')
            
            # Create credential structure
            cred = {
                'Type': self._win32cred.CRED_TYPE_GENERIC,
                'TargetName': f'VPNClient:{service_name}',
                'UserName': 'VPNClient',
                'CredentialBlob': cred_blob,
                'Persist': self._win32cred.CRED_PERSIST_LOCAL_MACHINE
            }
            
            # Store the credential
            self._win32cred.CredWrite(cred, 0)
            return True
        except Exception:
            return False
    
    def retrieve_credentials(self, service_name: str) -> Optional[Dict[str, str]]:
        """Retrieve credentials from Windows Credential Manager."""
        try:
            # Retrieve the credential
            cred = self._win32cred.CredRead(
                f'VPNClient:{service_name}',
                self._win32cred.CRED_TYPE_GENERIC,
                0
            )
            
            # Decode and parse the credential blob
            cred_blob = cred['CredentialBlob']
            credentials = json.loads(cred_blob.decode('utf-8'))
            return credentials
        except Exception:
            return None
    
    def delete_credentials(self, service_name: str) -> bool:
        """Delete credentials from Windows Credential Manager."""
        try:
            self._win32cred.CredDelete(
                f'VPNClient:{service_name}',
                self._win32cred.CRED_TYPE_GENERIC,
                0
            )
            return True
        except Exception:
            return False


class MacOSCredentialStorage(CredentialStorage):
    """macOS-specific implementation using Keychain."""
    
    def __init__(self):
        """Initialize the macOS credential storage."""
        try:
            import keyring
            self._keyring = keyring
        except ImportError:
            raise ImportError("The 'keyring' package is required for macOS credential storage.")
    
    def store_credentials(self, service_name: str, credentials: Dict[str, str]) -> bool:
        """Store credentials using macOS Keychain."""
        try:
            # Convert credentials to JSON string
            cred_json = json.dumps(credentials)
            
            # Store in keychain
            self._keyring.set_password('VPNClient', service_name, cred_json)
            return True
        except Exception:
            return False
    
    def retrieve_credentials(self, service_name: str) -> Optional[Dict[str, str]]:
        """Retrieve credentials from macOS Keychain."""
        try:
            # Retrieve from keychain
            cred_json = self._keyring.get_password('VPNClient', service_name)
            if not cred_json:
                return None
            
            # Parse JSON
            credentials = json.loads(cred_json)
            return credentials
        except Exception:
            return None
    
    def delete_credentials(self, service_name: str) -> bool:
        """Delete credentials from macOS Keychain."""
        try:
            self._keyring.delete_password('VPNClient', service_name)
            return True
        except Exception:
            return False


class LinuxCredentialStorage(CredentialStorage):
    """Linux-specific implementation using Secret Service API."""
    
    def __init__(self):
        """Initialize the Linux credential storage."""
        try:
            import secretstorage
            self._secretstorage = secretstorage
            self._connection = secretstorage.dbus_init()
            self._collection = secretstorage.get_default_collection(self._connection)
        except ImportError:
            raise ImportError("The 'secretstorage' package is required for Linux credential storage.")
    
    def store_credentials(self, service_name: str, credentials: Dict[str, str]) -> bool:
        """Store credentials using Secret Service API."""
        try:
            # Convert credentials to JSON string
            cred_json = json.dumps(credentials)
            
            # Create attributes dictionary
            attributes = {
                'application': 'VPNClient',
                'service': service_name
            }
            
            # Check if credential already exists
            items = list(self._collection.search_items(attributes))
            if items:
                # Update existing item
                items[0].set_secret(cred_json.encode('utf-8'))
            else:
                # Create new item
                self._collection.create_item(
                    f'VPNClient:{service_name}',
                    attributes,
                    cred_json.encode('utf-8'),
                    replace=True
                )
            
            return True
        except Exception:
            return False
    
    def retrieve_credentials(self, service_name: str) -> Optional[Dict[str, str]]:
        """Retrieve credentials from Secret Service API."""
        try:
            # Search for the credential
            attributes = {
                'application': 'VPNClient',
                'service': service_name
            }
            items = list(self._collection.search_items(attributes))
            
            if not items:
                return None
            
            # Get the secret
            secret = items[0].get_secret()
            cred_json = secret.decode('utf-8')
            
            # Parse JSON
            credentials = json.loads(cred_json)
            return credentials
        except Exception:
            return None
    
    def delete_credentials(self, service_name: str) -> bool:
        """Delete credentials from Secret Service API."""
        try:
            # Search for the credential
            attributes = {
                'application': 'VPNClient',
                'service': service_name
            }
            items = list(self._collection.search_items(attributes))
            
            if not items:
                return False
            
            # Delete the item
            items[0].delete()
            return True
        except Exception:
            return False


class AndroidCredentialStorage(CredentialStorage):
    """Android-specific implementation using Android Keystore."""
    
    def __init__(self):
        """Initialize the Android credential storage."""
        try:
            from jnius import autoclass
            self._Context = autoclass('android.content.Context')
            self._KeyStore = autoclass('java.security.KeyStore')
            self._KeyGenParameterSpec = autoclass('android.security.keystore.KeyGenParameterSpec')
            self._KeyProperties = autoclass('android.security.keystore.KeyProperties')
            self._KeyGenerator = autoclass('javax.crypto.KeyGenerator')
            self._Cipher = autoclass('javax.crypto.Cipher')
            self._SharedPreferences = autoclass('android.content.SharedPreferences')
            self._Base64 = autoclass('android.util.Base64')
        except ImportError:
            raise ImportError("The 'pyjnius' package is required for Android credential storage.")
    
    def store_credentials(self, service_name: str, credentials: Dict[str, str]) -> bool:
        """Store credentials using Android Keystore."""
        try:
            # Convert credentials to JSON string
            cred_json = json.dumps(credentials)
            
            # Get the Android context
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            
            # Get shared preferences
            prefs = context.getSharedPreferences('VPNClient', self._Context.MODE_PRIVATE)
            editor = prefs.edit()
            
            # Generate a key if it doesn't exist
            keystore = self._KeyStore.getInstance('AndroidKeyStore')
            keystore.load(None)
            
            key_alias = f'VPNClient_{service_name}'
            
            if not keystore.containsAlias(key_alias):
                key_generator = self._KeyGenerator.getInstance(
                    self._KeyProperties.KEY_ALGORITHM_AES, 'AndroidKeyStore')
                key_generator.init(
                    self._KeyGenParameterSpec.Builder(
                        key_alias,
                        self._KeyProperties.PURPOSE_ENCRYPT | self._KeyProperties.PURPOSE_DECRYPT
                    )
                    .setBlockModes(self._KeyProperties.BLOCK_MODE_CBC)
                    .setEncryptionPaddings(self._KeyProperties.ENCRYPTION_PADDING_PKCS7)
                    .build()
                )
                key_generator.generateKey()
            
            # Encrypt the credentials
            cipher = self._Cipher.getInstance(
                f"{self._KeyProperties.KEY_ALGORITHM_AES}/{self._KeyProperties.BLOCK_MODE_CBC}/{self._KeyProperties.ENCRYPTION_PADDING_PKCS7}"
            )
            cipher.init(self._Cipher.ENCRYPT_MODE, keystore.getKey(key_alias, None))
            
            encrypted_bytes = cipher.doFinal(cred_json.encode('utf-8'))
            iv = cipher.getIV()
            
            # Store the encrypted data and IV
            editor.putString(f"{service_name}_data", self._Base64.encodeToString(encrypted_bytes, 0))
            editor.putString(f"{service_name}_iv", self._Base64.encodeToString(iv, 0))
            editor.apply()
            
            return True
        except Exception:
            return False
    
    def retrieve_credentials(self, service_name: str) -> Optional[Dict[str, str]]:
        """Retrieve credentials from Android Keystore."""
        try:
            # Get the Android context
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            
            # Get shared preferences
            prefs = context.getSharedPreferences('VPNClient', self._Context.MODE_PRIVATE)
            
            # Get the encrypted data and IV
            encrypted_data_str = prefs.getString(f"{service_name}_data", None)
            iv_str = prefs.getString(f"{service_name}_iv", None)
            
            if not encrypted_data_str or not iv_str:
                return None
            
            encrypted_data = self._Base64.decode(encrypted_data_str, 0)
            iv = self._Base64.decode(iv_str, 0)
            
            # Get the key from the keystore
            keystore = self._KeyStore.getInstance('AndroidKeyStore')
            keystore.load(None)
            
            key_alias = f'VPNClient_{service_name}'
            if not keystore.containsAlias(key_alias):
                return None
            
            # Decrypt the data
            cipher = self._Cipher.getInstance(
                f"{self._KeyProperties.KEY_ALGORITHM_AES}/{self._KeyProperties.BLOCK_MODE_CBC}/{self._KeyProperties.ENCRYPTION_PADDING_PKCS7}"
            )
            cipher.init(self._Cipher.DECRYPT_MODE, keystore.getKey(key_alias, None), 
                       self._IvParameterSpec(iv))
            
            decrypted_bytes = cipher.doFinal(encrypted_data)
            cred_json = decrypted_bytes.decode('utf-8')
            
            # Parse JSON
            credentials = json.loads(cred_json)
            return credentials
        except Exception:
            return None
    
    def delete_credentials(self, service_name: str) -> bool:
        """Delete credentials from Android Keystore."""
        try:
            # Get the Android context
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            
            # Get shared preferences
            prefs = context.getSharedPreferences('VPNClient', self._Context.MODE_PRIVATE)
            editor = prefs.edit()
            
            # Remove the encrypted data and IV
            editor.remove(f"{service_name}_data")
            editor.remove(f"{service_name}_iv")
            editor.apply()
            
            # Remove the key from the keystore
            keystore = self._KeyStore.getInstance('AndroidKeyStore')
            keystore.load(None)
            
            key_alias = f'VPNClient_{service_name}'
            if keystore.containsAlias(key_alias):
                keystore.deleteEntry(key_alias)
            
            return True
        except Exception:
            return False


class FallbackCredentialStorage(CredentialStorage):
    """Fallback implementation using file-based storage with basic encryption.
    
    Note: This is less secure than platform-specific solutions and should only be used
    when other methods are not available.
    """
    
    def __init__(self, storage_dir: str = None):
        """Initialize the fallback credential storage.
        
        Args:
            storage_dir: Directory to store the encrypted credentials file.
                         If None, uses the user's home directory.
        """
        import hashlib
        from cryptography.fernet import Fernet
        
        self._hashlib = hashlib
        self._Fernet = Fernet
        
        # Set up storage directory
        if storage_dir is None:
            self._storage_dir = os.path.join(os.path.expanduser('~'), '.vpnclient')
        else:
            self._storage_dir = storage_dir
        
        # Create directory if it doesn't exist
        os.makedirs(self._storage_dir, exist_ok=True)
        
        # Set up encryption key
        key_file = os.path.join(self._storage_dir, '.key')
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self._key = f.read()
        else:
            # Generate a new key
            self._key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self._key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
        
        self._cipher = self._Fernet(self._key)
    
    def store_credentials(self, service_name: str, credentials: Dict[str, str]) -> bool:
        """Store credentials using file-based storage with encryption."""
        try:
            # Convert credentials to JSON string
            cred_json = json.dumps(credentials)
            
            # Encrypt the credentials
            encrypted_data = self._cipher.encrypt(cred_json.encode('utf-8'))
            
            # Store in file
            file_path = os.path.join(self._storage_dir, self._hash_service_name(service_name))
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(file_path, 0o600)
            
            return True
        except Exception:
            return False
    
    def retrieve_credentials(self, service_name: str) -> Optional[Dict[str, str]]:
        """Retrieve credentials from file-based storage."""
        try:
            file_path = os.path.join(self._storage_dir, self._hash_service_name(service_name))
            
            if not os.path.exists(file_path):
                return None
            
            # Read and decrypt the data
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self._cipher.decrypt(encrypted_data)
            cred_json = decrypted_data.decode('utf-8')
            
            # Parse JSON
            credentials = json.loads(cred_json)
            return credentials
        except Exception:
            return None
    
    def delete_credentials(self, service_name: str) -> bool:
        """Delete credentials from file-based storage."""
        try:
            file_path = os.path.join(self._storage_dir, self._hash_service_name(service_name))
            
            if not os.path.exists(file_path):
                return False
            
            # Delete the file
            os.remove(file_path)
            return True
        except Exception:
            return False
    
    def _hash_service_name(self, service_name: str) -> str:
        """Hash the service name to create a filename."""
        return self._hashlib.sha256(service_name.encode('utf-8')).hexdigest()


def get_credential_storage() -> CredentialStorage:
    """Factory function to get the appropriate credential storage implementation for the current platform.
    
    Returns:
        CredentialStorage: An instance of the appropriate credential storage implementation.
    """
    system = platform.system()
    
    try:
        if system == 'Windows':
            return WindowsCredentialStorage()
        elif system == 'Darwin':  # macOS
            return MacOSCredentialStorage()
        elif system == 'Linux':
            # Check if running on Android
            if 'ANDROID_ROOT' in os.environ:
                return AndroidCredentialStorage()
            else:
                return LinuxCredentialStorage()
        else:
            # Fallback for unsupported platforms
            return FallbackCredentialStorage()
    except ImportError as e:
        print(f"Warning: {e}. Using fallback credential storage.", file=sys.stderr)
        return FallbackCredentialStorage()