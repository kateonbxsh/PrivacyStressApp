-- CreateTable
CREATE TABLE IF NOT EXISTS "User" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "email" TEXT NOT NULL,
    "passwordHash" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "SensitiveProfile" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "encryptedVector" BLOB NOT NULL,
    "vectorIv" BLOB NOT NULL,
    "vectorAuthTag" BLOB NOT NULL,
    "wrappedDek" BLOB NOT NULL,
    "wrappedDekIv" BLOB NOT NULL,
    "wrappedDekAuthTag" BLOB NOT NULL,
    "salt" BLOB NOT NULL,
    "vectorDimension" INTEGER NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "UserProfileLink" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "profileId" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "UserProfileLink_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "UserProfileLink_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "SensitiveProfile" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS "User_email_key" ON "User"("email");
CREATE UNIQUE INDEX IF NOT EXISTS "UserProfileLink_userId_key" ON "UserProfileLink"("userId");
CREATE UNIQUE INDEX IF NOT EXISTS "UserProfileLink_profileId_key" ON "UserProfileLink"("profileId");
