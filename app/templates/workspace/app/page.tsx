"use client"

import { useState, useEffect, useRef } from "react"
import { useSearchParams } from "next/navigation"
import { io, Socket } from "socket.io-client"

export default function Game() {
  const searchParams = useSearchParams()
  const [board, setBoard] = useState<(string | null)[]>(Array(9).fill(null))
  const [currentTurn, setCurrentTurn] = useState<string>("")
  const [winner, setWinner] = useState<string | null>(null)
  const [room, setRoom] = useState<any>(null)
  const [currentPlayer, setCurrentPlayer] = useState<any>(null)
  const [opponent, setOpponent] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [gameOver, setGameOver] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState("Connecting...")
  const socketRef = useRef<Socket | null>(null)

  const gameSessionUuid = searchParams?.get("gameSessionUuid")
  const playerUuid = searchParams?.get("uuid")

  useEffect(() => {
    if (gameSessionUuid && playerUuid) {
      initializeGame()
    }
  }, [gameSessionUuid, playerUuid])

  useEffect(() => {
    if (gameSessionUuid && playerUuid) {
      const socket = io({
        path: "/api/socket",
      })
      socketRef.current = socket

      socket.on("connect", () => {
        setConnectionStatus("Connected")
        socket.emit("join-game", { gameSessionUuid, playerUuid })
      })

      socket.on("player-joined", ({ playerUuid: joinedPlayerUuid }) => {
        console.log(`Player joined: ${joinedPlayerUuid}`)
        if (!opponent) {
          initializeGame()
        }
      })

      socket.on("move-made", ({ playerUuid: movePlayer, position, gameBoard, currentTurn }) => {
        setBoard(gameBoard)
        setCurrentTurn(currentTurn)
        const calculatedWinner = calculateWinner(gameBoard)
        if (calculatedWinner) {
          setWinner(calculatedWinner)
          setGameOver(true)
        } else if (gameBoard.every((square: string | null) => square !== null)) {
          setGameOver(true)
        }
      })

      socket.on("game-ended", ({ winner }) => {
        setWinner(winner)
        setGameOver(true)
      })

      socket.on("disconnect", () => {
        setConnectionStatus("Disconnected")
      })

      socket.on("connect_error", () => {
        setConnectionStatus("Connection Error")
      })

      return () => {
        socket.disconnect()
        socketRef.current = null
      }
    }
  }, [gameSessionUuid, playerUuid]) // Removed opponent from deps to prevent reconnections

  const initializeGame = async () => {
    try {
      const response = await fetch(`/api/get-room?gameSessionUuid=${gameSessionUuid}`)
      const data = await response.json()

      if (data.status && data.payload) {
        setRoom(data.payload)
        setBoard(data.payload.gameBoard || Array(9).fill(null))
        setCurrentTurn(data.payload.currentTurn)
        setWinner(data.payload.winner)

        const current = data.payload.players.find((p: any) => p.uuid === playerUuid)
        const opp = data.payload.players.find((p: any) => p.uuid !== playerUuid)

        setCurrentPlayer(current || null)
        setOpponent(opp || null)

        if (data.payload.winner || data.payload.gameBoard?.every((square: string | null) => square !== null)) {
          setGameOver(true)
        }
      }
      setLoading(false)
    } catch (error) {
      console.error("Error fetching room data:", error)
      setLoading(false)
      setConnectionStatus("Connection Error")
    }
  }

  const calculateWinner = (squares: (string | null)[]) => {
    const lines = [
      [0, 1, 2],
      [3, 4, 5],
      [6, 7, 8],
      [0, 3, 6],
      [1, 4, 7],
      [2, 5, 8],
      [0, 4, 8],
      [2, 4, 6],
    ]

    for (let i = 0; i < lines.length; i++) {
      const [a, b, c] = lines[i]
      if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
        return squares[a]
      }
    }
    return null
  }

  const handleClick = (i: number) => {
    if (calculateWinner(board) || board[i] || gameOver || currentTurn !== playerUuid || !socketRef.current?.connected) {
      return
    }

    const symbol = room.players[0].uuid === playerUuid ? "X" : "O"
    const newBoard = [...board]
    newBoard[i] = symbol
    const newCurrentTurn = opponent.uuid // Switch to opponent

    setBoard(newBoard)
    setCurrentTurn(newCurrentTurn)

    socketRef.current?.emit("make-move", {
      gameSessionUuid,
      playerUuid,
      position: i,
      gameBoard: newBoard,
      currentTurn: newCurrentTurn,
    })

    const gameWinner = calculateWinner(newBoard)
    if (gameWinner) {
      const winnerPlayer = gameWinner === "X" ? room.players[0] : room.players[1]
      setWinner(gameWinner)
      setGameOver(true)

      sendWinnerData(winnerPlayer.uuid)

      socketRef.current?.emit("game-won", { gameSessionUuid, winner: gameWinner })
    } else if (newBoard.every((square: string | null) => square !== null)) {
      setGameOver(true)
      socketRef.current?.emit("game-won", { gameSessionUuid, winner: null })
    }
  }

  const sendWinnerData = async (winnerUuid: string) => {
    try {
      const response = await fetch("/api/send-winner", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          gameSessionUuid,
          winner: winnerUuid,
        }),
      })

      const result = await response.json()
      console.log("Winner data sent:", result)
    } catch (error) {
      console.error("Error sending winner data:", error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl mb-2">Loading game...</div>
          <div className="text-sm text-gray-600">{connectionStatus}</div>
        </div>
      </div>
    )
  }

  if (!room || !currentPlayer || !opponent) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl text-red-600">Error: Could not load game data</div>
      </div>
    )
  }

  const gameWinner = calculateWinner(board)
  const isDraw = !gameWinner && board.every((square) => square !== null)
  const isMyTurn = currentTurn === playerUuid

  let status
  if (gameWinner) {
    const winnerPlayer = gameWinner === "X" ? room.players[0] : room.players[1]
    status = `🎉 Winner: ${winnerPlayer.name}!`
  } else if (isDraw) {
    status = "🤝 Game Draw!"
  } else {
    const currentPlayerName = room.players.find((p: any) => p.uuid === currentTurn)?.name
    status = isMyTurn ? "🎯 Your Turn!" : `⏳ Waiting for ${currentPlayerName}...`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-4 text-gray-800">🎮 Multiplayer Tic-Tac-Toe</h1>

        {/* Connection Status */}
        <div className="text-center mb-6">
          <div
            className={`text-sm px-3 py-1 rounded-full inline-block ${
              connectionStatus.includes("Connected")
                ? "bg-green-100 text-green-800"
                : connectionStatus.includes("Error") || connectionStatus.includes("Disconnected")
                  ? "bg-red-100 text-red-800"
                  : "bg-yellow-100 text-yellow-800"
            }`}
          >
            {connectionStatus}
          </div>
        </div>

        {/* Players Info */}
        <div className="flex justify-between items-center mb-8 bg-white rounded-xl p-6 shadow-lg">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <img
                src={room.players[0].profileImage || "/placeholder.svg?height=80&width=80"}
                alt={room.players[0].name}
                className="w-16 h-16 rounded-full border-4 border-blue-500 object-cover"
              />
              {currentTurn === room.players[0].uuid && !gameOver && (
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-pulse"></div>
              )}
            </div>
            <div>
              <h3 className="font-bold text-xl text-gray-800">{room.players[0].name}</h3>
              <p className="text-blue-600 font-semibold">Player X</p>
              {playerUuid === room.players[0].uuid && <p className="text-sm text-green-600 font-medium">👤 You</p>}
            </div>
          </div>

          <div className="text-center">
            <div className="text-3xl font-bold text-gray-600">VS</div>
            <div className="text-sm text-gray-500 mt-1">Room: {gameSessionUuid?.slice(-6)}</div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-right">
              <h3 className="font-bold text-xl text-gray-800">{room.players[1].name}</h3>
              <p className="text-red-600 font-semibold">Player O</p>
              {playerUuid === room.players[1].uuid && <p className="text-sm text-green-600 font-medium">👤 You</p>}
            </div>
            <div className="relative">
              <img
                src={room.players[1].profileImage || "/placeholder.svg?height=80&width=80"}
                alt={room.players[1].name}
                className="w-16 h-16 rounded-full border-4 border-red-500 object-cover"
              />
              {currentTurn === room.players[1].uuid && !gameOver && (
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-pulse"></div>
              )}
            </div>
          </div>
        </div>

        {/* Game Status */}
        <div className="text-center mb-8">
          <div className="text-2xl font-bold mb-2 text-gray-800">{status}</div>
          {!gameOver && (
            <div className={`text-lg ${isMyTurn ? "text-green-600" : "text-orange-600"}`}>
              {isMyTurn ? "🎯 Make your move!" : "⏳ Wait for opponent..."}
            </div>
          )}
        </div>

        {/* Game Board */}
        <div className="flex justify-center mb-8">
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="grid grid-cols-3 gap-2">
              {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                <button
                  key={i}
                  className={`w-20 h-20 text-3xl font-bold rounded-lg border-2 transition-all duration-200 ${
                    board[i]
                      ? board[i] === "X"
                        ? "bg-blue-100 border-blue-500 text-blue-600"
                        : "bg-red-100 border-red-500 text-red-600"
                      : isMyTurn && !gameOver
                        ? "bg-gray-50 border-gray-300 hover:bg-gray-100 hover:border-gray-400 cursor-pointer"
                        : "bg-gray-50 border-gray-300 cursor-not-allowed opacity-50"
                  }`}
                  onClick={() => handleClick(i)}
                  disabled={!isMyTurn || gameOver || board[i] !== null}
                >
                  {board[i]}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Game Over Actions */}
        {gameOver && (
          <div className="text-center">
            <div className="bg-white rounded-xl p-6 shadow-lg inline-block">
              <div className="text-xl font-semibold mb-4">
                {winner ? (
                  <span className="text-green-600">
                    🎉{" "}
                    {
                      room.players.find((p: any) => (winner === "X" ? p === room.players[0] : p === room.players[1]))
                        ?.name
                    }{" "}
                    Wins!
                  </span>
                ) : (
                  <span className="text-yellow-600">🤝 It's a Draw!</span>
                )}
              </div>
              <button
                onClick={() => window.location.reload()}
                className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                🔄 Play Again
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}