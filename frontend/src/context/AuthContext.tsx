import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

// We'll store the Firebase user type loosely to avoid import issues when Firebase isn't configured
interface FirebaseUser {
  displayName: string | null;
  email: string | null;
  uid: string;
  getIdToken: () => Promise<string>;
  getIdTokenResult: () => Promise<{ claims: Record<string, any> }>;
}

interface AuthContextType {
  user: FirebaseUser | null;
  role: string;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  role: 'senior_officer',
  loading: false,
  signInWithGoogle: async () => {},
  logout: async () => {},
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [role, setRole] = useState('senior_officer');
  const [loading, setLoading] = useState(true);
  const [firebaseReady, setFirebaseReady] = useState(false);
  const [authInstance, setAuthInstance] = useState<any>(null);
  const [providerInstance, setProviderInstance] = useState<any>(null);

  // Initialize Firebase lazily
  useEffect(() => {
    const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;
    const projectId = import.meta.env.VITE_FIREBASE_PROJECT_ID;

    if (!apiKey || !projectId) {
      console.warn('Firebase config not provided — running in demo mode without auth');
      setLoading(false);
      return;
    }

    const initFirebase = async () => {
      try {
        const { initializeApp } = await import('firebase/app');
        const { getAuth, GoogleAuthProvider, onAuthStateChanged } = await import('firebase/auth');

        const app = initializeApp({
          apiKey,
          authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
          projectId,
          storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '',
          messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
          appId: import.meta.env.VITE_FIREBASE_APP_ID || '',
        });

        const authObj = getAuth(app);
        const provider = new GoogleAuthProvider();

        setAuthInstance(authObj);
        setProviderInstance(provider);
        setFirebaseReady(true);

        onAuthStateChanged(authObj, async (firebaseUser) => {
          if (firebaseUser) {
            setUser(firebaseUser as unknown as FirebaseUser);
            const tokenResult = await firebaseUser.getIdTokenResult();
            setRole((tokenResult.claims.role as string) || 'senior_officer');
          } else {
            setUser(null);
            setRole('senior_officer');
          }
          setLoading(false);
        });
      } catch (e) {
        console.warn('Firebase initialization failed:', e);
        setLoading(false);
      }
    };

    initFirebase();
  }, []);

  const signInWithGoogle = async () => {
    if (!firebaseReady || !authInstance || !providerInstance) {
      alert('Firebase is not configured. Set VITE_FIREBASE_* environment variables to enable authentication.');
      return;
    }
    try {
      const { signInWithPopup } = await import('firebase/auth');
      await signInWithPopup(authInstance, providerInstance);
    } catch (error) {
      console.error('Sign in failed:', error);
    }
  };

  const logout = async () => {
    if (authInstance) {
      const { signOut } = await import('firebase/auth');
      await signOut(authInstance);
    }
    setUser(null);
    setRole('senior_officer');
  };

  return (
    <AuthContext.Provider value={{ user, role, loading, signInWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
