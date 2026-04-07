FROM oven/bun:latest AS builder

WORKDIR /opt/app

COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile

COPY . ./

ENV NEXT_PUBLIC_BACKEND_URL=https://cerebrational-lyman-cavate.ngrok-free.dev
RUN bun run build

FROM oven/bun:latest

WORKDIR /opt/app

COPY --from=builder /opt/app/.next ./.next
COPY --from=builder /opt/app/node_modules ./node_modules
COPY --from=builder /opt/app/package.json ./
COPY --from=builder /opt/app/public ./public

EXPOSE 22091

CMD ["bun", "run", "start", "--port", "22091"]
