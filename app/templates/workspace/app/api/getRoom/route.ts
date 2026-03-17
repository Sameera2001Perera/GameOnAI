import { type NextRequest, NextResponse } from "next/server"
import dbConnect from "@/lib/mongodb"
import Room from "@/lib/models/Room"

export async function GET(request: NextRequest) {
  try {
    await dbConnect()

    const { searchParams } = new URL(request.url)
    const gameSessionUuid = searchParams.get("gameSessionUuid")

    if (!gameSessionUuid) {
      return NextResponse.json(
        {
          status: false,
          message: "gameSessionUuid is required",
        },
        { status: 400 },
      )
    }

    const room = await Room.findOne({ gameSessionUuid })

    if (!room) {
      return NextResponse.json(
        {
          status: false,
          message: "Room not found",
        },
        { status: 404 },
      )
    }

    return NextResponse.json({
      status: true,
      message: "success",
      payload: room,
    })
  } catch (error) {
    console.error("Error fetching room:", error)
    return NextResponse.json(
      {
        status: false,
        message: "Error fetching room",
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}
